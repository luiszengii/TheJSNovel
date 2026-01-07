《第 66 次记录: JSON 序列化事故 —— 信息丢失》

---

## 数据恢复失败

周五下午三点, 数据库运维组发出紧急通知:"今早凌晨 2 点的数据库备份脚本出错, 需要从昨晚 10 点的备份恢复部分数据。"

你负责的用户状态系统受到影响。运维老王找到你:"能从备份文件恢复用户状态吗? 我们已经把 JSON 备份文件发到你邮箱了。"

"没问题," 你打开邮件, 下载了备份文件 `user-states-backup.json`, "我写个脚本导入就行。"

你打开备份文件, 是一个包含 5000+ 用户状态的 JSON 数组。每个用户状态对象大概长这样:

```json
{
  "userId":1001,
  "username":"zhangsan",
  "loginTime":1699632000000,
  "preferences":{
    "theme":"dark",
    "language":"zh-CN"
  },
  "status":"active"
}
```

看起来很正常。你写了一个简单的导入脚本:

```javascript
// restore-data.js
const fs = require('fs');

const backupData = fs.readFileSync('user-states-backup.json', 'utf8');
const users = JSON.parse(backupData);

console.log(`准备恢复 ${users.length} 个用户的状态...`);

users.forEach(user => {
    database.updateUserState(user.userId, user);
});

console.log('恢复完成!');
```

脚本执行成功, 没有报错。但十分钟后, 客服部门发来一连串投诉。

---

## 用户投诉

下午三点半, 客服主管小刘拿着一叠截图冲进办公室。

"出大问题了!" 小刘说, "用户反馈他们的自定义设置全部丢失了。"

你心里一惊:"什么设置丢失了?"

"VIP 用户的自定义功能、高级筛选器、保存的搜索条件, 全都没了," 小刘说, "这些用户很生气, 说辛苦配置了几个月的设置一夜之间全部消失。"

你立刻检查数据库, 发现确实有问题。一个 VIP 用户的状态对象应该是这样的:

```javascript
// 预期的完整用户状态
{
    userId:1001,
    username:"zhangsan",
    loginTime:1699632000000,
    customFilters:[
        function(item) { return item.price > 100;},
        function(item) { return item.category === 'electronics';}
    ],
    preferences:{
        theme:"dark",
        language:"zh-CN",
        updateCallback:function() { console.log('Updated');}
    },
    metadata:{
        lastLogin:new Date('2024-11-10T10:00:00Z'),
        vipLevel:3,
        points:undefined  // 未初始化
    }
}
```

但恢复后的数据变成了:

```javascript
// 实际恢复后的数据
{
    userId:1001,
    username:"zhangsan",
    loginTime:1699632000000,
    preferences:{
        theme:"dark",
        language:"zh-CN"
    }
    // customFilters:完全丢失!
    // metadata.updateCallback:丢失!
    // metadata.lastLogin:变成了字符串!
    // metadata.points:丢失!
}
```

"函数、undefined、Date 对象... 全都不见了," 你倒吸一口凉气。

---

## JSON 的限制

下午四点, 老张赶来帮忙分析。

"JSON 不是万能的," 老张说, "它只能序列化部分 JavaScript 类型。"

他在白板上列出 JSON 支持和不支持的类型:

```
JSON 支持的类型:
✅ 字符串 (String)
✅ 数字 (Number) - 但 NaN, Infinity 会变成 null
✅ 布尔值 (Boolean)
✅ 对象 (Object) - 只序列化可枚举属性
✅ 数组 (Array)
✅ null

JSON 不支持的类型 (会丢失或转换):
❌ undefined - 直接丢失
❌ 函数 (Function) - 直接丢失
❌ Symbol - 直接丢失
❌ Date 对象 - 转成字符串
❌ RegExp 对象 - 转成空对象 {}
❌ Map, Set - 转成空对象 {}
❌ NaN, Infinity - 转成 null
❌ 循环引用 - 报错
```

"我们的备份脚本当时是怎么生成 JSON 的?" 你问。

老张找出备份脚本:

```javascript
// backup.js - 问题脚本
const users = await database.getAllUserStates();

const json = JSON.stringify(users);
fs.writeFileSync('user-states-backup.json', json);
```

"就这么简单?" 你惊讶, "`JSON.stringify()` 会自动丢弃不支持的类型?"

"对," 老张点头, "而且没有任何警告。"

---

## 测试序列化

下午四点半, 你开始系统测试 JSON 序列化行为。

```javascript
// 测试 1:各种类型的序列化
const testObj = {
    string:"hello",
    number:42,
    boolean:true,
    null:null,
    undefined:undefined,      // 将丢失
    func:function() {},       // 将丢失
    symbol:Symbol('test'),    // 将丢失
    date:new Date(),          // 转成字符串
    regex:/test/,             // 转成 {}
    nan:NaN,                  // 转成 null
    infinity:Infinity,        // 转成 null
    map:new Map([['a', 1]]), // 转成 {}
    set:new Set([1, 2, 3])     // 转成 {}
};

const json = JSON.stringify(testObj, null, 2);
console.log(json);
```

输出结果:

```json
{
  "string":"hello",
  "number":42,
  "boolean":true,
  "null":null,
  "date":"2024-11-15T08:30:00.000Z",
  "regex":{},
  "nan":null,
  "infinity":null,
  "map":{},
  "set":{}
}
```

"看," 你指着输出, "`undefined`、`func`、`symbol` 完全消失了。`date` 变成字符串, `regex`、`map`、`set` 变成空对象。"

"更糟糕的是数组," 老张补充:

```javascript
// 测试 2:数组中的特殊值
const arr = [1, undefined, function() {}, Symbol('x'), 2];

console.log(JSON.stringify(arr));
// [1, null, null, null, 2]
// undefined、函数、Symbol 都变成了 null
```

"数组中会保留位置, 但用 `null` 占位," 老张说, "这会导致数组长度对不上。"

---

## 循环引用问题

下午五点, 测试小林发现了另一个严重问题。

"如果对象有循环引用会怎样?" 小林问。

老张演示:

```javascript
const obj = { name:'test' };
obj.self = obj; // 循环引用

try {
    JSON.stringify(obj);
} catch (e) {
    console.error(e.message);
    // TypeError:Converting circular structure to JSON
}
```

"直接报错," 老张说, "而且是运行时错误, 没办法提前检测。"

"我们的用户状态对象可能有循环引用吗?" 你突然想到。

你检查代码, 发现确实有:

```javascript
// user-state.js - 可能存在循环引用
class UserState {
    constructor(userId) {
        this.userId = userId;
        this.parent = null;
        this.children = [];
    }

    addChild(childState) {
        childState.parent = this; // 循环引用!
        this.children.push(childState);
    }
}
```

"如果用户状态有父子关系, 序列化就会失败," 你说, "难怪有些用户的备份根本没生成。"

---

## 安全序列化方案

下午五点半, 老张开始设计安全的序列化方案。

"我们需要自定义序列化逻辑," 老张说, "使用 `JSON.stringify()` 的第二个参数 —— replacer 函数。"

```javascript
// safe-serialize.js - 安全序列化方案

/**
 * 自定义 replacer 函数
 */
function createReplacer() {
    const seen = new WeakSet(); // 检测循环引用

    return function(key, value) {
        // 处理循环引用
        if (typeof value === 'object' && value !== null) {
            if (seen.has(value)) {
                return '[Circular]';
            }
            seen.add(value);
        }

        // 保留函数 (转成字符串)
        if (typeof value === 'function') {
            return {
                __type:'Function',
                __source:value.toString()
            };
        }

        // 保留 Date
        if (value instanceof Date) {
            return {
                __type:'Date',
                __value:value.getTime()
            };
        }

        // 保留 RegExp
        if (value instanceof RegExp) {
            return {
                __type:'RegExp',
                __source:value.source,
                __flags:value.flags
            };
        }

        // 保留 Map
        if (value instanceof Map) {
            return {
                __type:'Map',
                __entries:Array.from(value.entries())
            };
        }

        // 保留 Set
        if (value instanceof Set) {
            return {
                __type:'Set',
                __values:Array.from(value.values())
            };
        }

        // 保留 undefined (特殊标记)
        if (value === undefined) {
            return { __type:'undefined' };
        }

        return value;
    };
}

// 使用
const userState = {
    userId:1001,
    loginTime:new Date(),
    customFilter:function(item) { return item.price > 100;},
    tags:new Set(['vip', 'premium']),
    metadata:new Map([['level', 3]]),
    points:undefined
};

const json = JSON.stringify(userState, createReplacer(), 2);
console.log(json);
```

输出:

```json
{
  "userId":1001,
  "loginTime":{
    "__type":"Date",
    "__value":1699632000000
  },
  "customFilter":{
    "__type":"Function",
    "__source":"function(item) { return item.price > 100;}"
  },
  "tags":{
    "__type":"Set",
    "__values":["vip", "premium"]
  },
  "metadata":{
    "__type":"Map",
    "__entries":[["level", 3]]
  },
  "points":{
    "__type":"undefined"
  }
}
```

"完美!" 你说, "现在所有类型都保留了。"

---

## 反序列化方案

下午六点, 你开始实现对应的反序列化 (reviver) 函数。

```javascript
// safe-deserialize.js - 安全反序列化

/**
 * 自定义 reviver 函数
 */
function createReviver() {
    return function(key, value) {
        if (typeof value === 'object' && value !== null && value.__type) {
            switch (value.__type) {
                case 'Function':
                    // 警告:eval 有安全风险, 生产环境需要沙箱
                    return new Function('return ' + value.__source)();

                case 'Date':
                    return new Date(value.__value);

                case 'RegExp':
                    return new RegExp(value.__source, value.__flags);

                case 'Map':
                    return new Map(value.__entries);

                case 'Set':
                    return new Set(value.__values);

                case 'undefined':
                    return undefined;

                default:
                    return value;
            }
        }

        return value;
    };
}

// 使用
const parsed = JSON.parse(json, createReviver());

console.log(parsed.loginTime instanceof Date); // true
console.log(parsed.tags instanceof Set); // true
console.log(parsed.metadata instanceof Map); // true
console.log(parsed.points === undefined); // true
console.log(typeof parsed.customFilter); // 'function'
```

"这样就能完整还原对象了," 老张说, "但要注意, 函数序列化有安全风险, 只能用于可信数据源。"

---

## toJSON 方法

下午六点半, 老张介绍了另一个方案。

"对象可以自定义 `toJSON()` 方法," 老张说, "控制自己如何被序列化。"

```javascript
// user-state-improved.js - 使用 toJSON

class UserState {
    constructor(userId) {
        this.userId = userId;
        this.loginTime = new Date();
        this.customFilters = [];
        this.metadata = new Map();
    }

    // 自定义序列化
    toJSON() {
        return {
            userId:this.userId,
            loginTime:this.loginTime.getTime(), // Date 转时间戳
            customFilters:this.customFilters.map(f => f.toString()),
            metadata:Array.from(this.metadata.entries())
        };
    }

    // 静态方法:从 JSON 还原
    static fromJSON(json) {
        const state = new UserState(json.userId);
        state.loginTime = new Date(json.loginTime);
        state.customFilters = json.customFilters.map(
            code => new Function('return ' + code)()
        );
        state.metadata = new Map(json.metadata);
        return state;
    }
}

// 使用
const state = new UserState(1001);
state.metadata.set('level', 3);

const json = JSON.stringify(state); // 自动调用 toJSON()
const restored = UserState.fromJSON(JSON.parse(json));
```

"这样更优雅," 你说, "对象自己知道如何序列化和还原。"

---

## 紧急修复

下午七点, 你完成了新的备份和恢复脚本。

```javascript
// backup-safe.js - 安全备份脚本
const users = await database.getAllUserStates();

const json = JSON.stringify(users, createReplacer(), 2);
fs.writeFileSync('user-states-backup-safe.json', json);

console.log('安全备份完成');

// restore-safe.js - 安全恢复脚本
const backupData = fs.readFileSync('user-states-backup-safe.json', 'utf8');
const users = JSON.parse(backupData, createReviver());

console.log(`准备恢复 ${users.length} 个用户...`);

users.forEach(user => {
    // 验证数据完整性
    if (!user.userId || !user.username) {
        console.error('数据不完整:', user);
        return;
    }

    database.updateUserState(user.userId, user);
});

console.log('恢复完成!');
```

"还要处理之前的用户投诉," 运维老王说, "能从旧备份恢复他们的设置吗?"

"旧备份数据已经丢失了," 你无奈地说, "函数和复杂对象都没了, 没办法完全恢复。"

"那只能让用户重新配置了," 老李说, "给受影响的 VIP 用户补偿一些积分吧。记住这次教训, 关键数据的序列化要格外小心。"

---

## 总结与反思

晚上八点, 事故处理完毕。你在笔记本上总结今天的教训。

**JSON 序列化的核心问题:**
- 只支持有限的数据类型
- 会静默丢弃不支持的类型
- 循环引用会导致错误
- Date、RegExp 等对象会被转换

**解决方案:**
1. 使用 replacer/reviver 自定义序列化
2. 实现 toJSON() 方法
3. 对关键数据使用专门的序列化库
4. 序列化前验证数据结构
5. 反序列化后验证数据完整性

你还列出了一个检查清单, 以后序列化数据前都要检查:

```
序列化前检查清单:
□ 数据中是否有函数?
□ 是否有 undefined 值?
□ 是否有 Date、RegExp 等特殊对象?
□ 是否有 Map、Set 等集合?
□ 是否可能有循环引用?
□ 是否需要保留所有信息?
```

你保存了文档, 决定明天写一个通用的安全序列化工具, 供整个团队使用。

---

## 知识总结

**规则 1: JSON 支持的类型**

JSON 只能序列化以下类型: 字符串、数字 (非 `NaN`/`Infinity`)、布尔值、`null`、数组、对象 (只序列化可枚举属性)。其他类型会丢失、转换或报错。

---

**规则 2: JSON 不支持的类型处理**

| 类型 | 序列化结果 | 对象中 | 数组中 |
|------|-----------|--------|--------|
| `undefined` | 丢失 | 直接丢失 | 转成 `null` |
| 函数 | 丢失 | 直接丢失 | 转成 `null` |
| Symbol | 丢失 | 直接丢失 | 转成 `null` |
| Date | 字符串 | ISO 字符串 | ISO 字符串 |
| RegExp | 空对象 | `{}` | `{}` |
| Map/Set | 空对象 | `{}` | `{}` |
| `NaN`/`Infinity` | `null` | `null` | `null` |

对象属性会丢失, 数组元素会保留位置但转成 `null`。

---

**规则 3: 循环引用处理**

循环引用会导致 `TypeError`, 需要手动检测和处理:

```javascript
function safeStringify(obj) {
    const seen = new WeakSet();
    return JSON.stringify(obj, (key, value) => {
        if (typeof value === 'object' && value !== null) {
            if (seen.has(value)) return '[Circular]';
            seen.add(value);
        }
        return value;
    });
}
```

使用 WeakSet 追踪已访问对象, 遇到循环引用时返回标记。

---

**规则 4: replacer 和 reviver 函数**

`JSON.stringify()` 第二个参数是 replacer 函数, 用于自定义序列化逻辑:

```javascript
JSON.stringify(obj, (key, value) => {
    if (value instanceof Date) {
        return { __type:'Date', __value:value.getTime() };
    }
    return value;
});
```

`JSON.parse()` 第二个参数是 reviver 函数, 用于还原自定义类型:

```javascript
JSON.parse(json, (key, value) => {
    if (value?.__type === 'Date') {
        return new Date(value.__value);
    }
    return value;
});
```

---

**规则 5: toJSON 方法**

对象可以实现 `toJSON()` 方法控制自己的序列化行为:

```javascript
class User {
    constructor(id, name) {
        this.id = id;
        this.name = name;
        this.password = 'secret'; // 敏感信息
    }

    toJSON() {
        return { id:this.id, name:this.name }; // 不包含 password
    }
}

JSON.stringify(new User(1, 'Zhang')); // {"id":1,"name":"Zhang"}
```

`toJSON()` 会在序列化时自动调用, 优先级高于默认行为。

---

**规则 6: 安全序列化检查清单**

序列化前检查:
- ✅ 数据类型是否都是 JSON 支持的
- ✅ 是否有循环引用
- ✅ 是否需要保留函数、Date 等特殊类型
- ✅ 是否有敏感信息需要过滤
- ✅ 数据量是否过大 (可能超出内存)

反序列化后验证:
- ✅ 数据完整性检查
- ✅ 类型验证 (Date 字符串需手动转换)
- ✅ 业务逻辑验证

---

**事故档案编号**: OBJ-2024-1866
**影响范围**: JSON 序列化, 数据备份, 函数丢失, Date 转换, 循环引用
**根本原因**: 使用 `JSON.stringify()` 备份包含函数和特殊对象的数据, 导致信息丢失
**修复成本**: 高 (数据不可完全恢复), 需用户重新配置, 影响用户体验

这是 JavaScript 世界第 66 次被记录的数据序列化事故。JSON 只支持有限类型: 字符串、数字、布尔、null、数组、对象。不支持的类型: undefined/函数/Symbol (丢失), Date (转字符串), RegExp/Map/Set (转空对象), NaN/Infinity (转 null)。循环引用会报错。解决方案: 使用 replacer/reviver 自定义序列化, 实现 toJSON() 方法, 使用 WeakSet 检测循环引用。序列化前检查数据类型, 反序列化后验证完整性。函数序列化有安全风险, 只用于可信数据。理解 JSON 的限制是安全数据传输和存储的基础。

---
