《第8次记录：属性双重身份事故 —— Attribute 与 Property 的分裂》

---

## 事故现场

周四下午四点，你盯着屏幕上的用户反馈表单已经盯了一个小时了。办公室里很安静，大部分人都去参加周会了，只剩下你和远处测试组的几个同事。

窗外开始飘起小雨，淅淅沥沥地打在玻璃上。你揉了揉眼睛,看向桌上已经凉透的咖啡。

产品经理半小时前发来消息："用户反馈说刷新页面后输入的内容全都丢了。这个'记住用户输入'的功能不是做好了吗?"

你快速回复:"在查了,应该是localStorage的问题。"但你心里没底。你明明测试过,本地环境运行得很好。

你打开代码,检查保存逻辑:

```javascript
const input = document.querySelector('#username');
localStorage.setItem('username', input.getAttribute('value'));
```

看起来没问题。你打开浏览器,在输入框里输入"张三",然后刷新页面——输入框变成了空白。

"怎么回事?"你喃喃自语。你按F12打开DevTools的Elements面板,看到HTML里明明写着:

```html
<input id="username" type="text" value="张三">
```

`value`属性就在那里,为什么输入框是空的?

测试同事走过来,看了一眼你的屏幕:"还在调这个?我刚才又测了几个表单,全都有这个问题。"

"我知道,"你的声音有些紧张,"我在排查原因。"

"产品经理说今天下班前要修好,明天要给客户演示。"测试同事拍了拍你的肩膀,"加油。"

你的心沉了下去。现在是下午四点,距离下班只有两个小时。你试着用JavaScript验证:

```javascript
console.log(input.getAttribute('value'));  // "张三"
console.log(input.value);                  // ""
```

同一个`value`,两种读取方式,两个完全不同的结果?

你突然想起之前做过的checkbox功能也有类似的奇怪现象。你快速测试了一下:

```javascript
const checkbox = document.querySelector('#agree');

// 用户点击勾选
console.log(checkbox.checked);              // true
console.log(checkbox.getAttribute('checked')); // null

// 用鼠标再点一次,取消勾选
console.log(checkbox.checked);              // false
console.log(checkbox.getAttribute('checked')); // "checked"
```

"attribute和property...不同步?"你盯着控制台的输出,感觉抓住了什么,但又说不清楚。

办公室里又安静下来。窗外的雨越下越大,你看了一眼时间——下午四点半了。

---

## 深入迷雾

你深吸一口气,决定彻底搞清楚attribute和property的关系。你创建了一个测试文件,从最基本的概念开始验证:

```javascript
const div = document.createElement('div');

// attribute: HTML标签上的文本属性
div.setAttribute('data-id', '123');
console.log(div.getAttribute('data-id'));  // "123"

// property: JavaScript对象上的属性
div.customProp = 'test';
console.log(div.customProp);  // "test"
console.log(div.getAttribute('customProp'));  // null
```

"所以它们是两个完全不同的系统,"你记下笔记,"attribute在HTML里,property在DOM对象上。"

你继续测试它们的同步关系:

```javascript
const input = document.createElement('input');
input.type = 'text';
document.body.appendChild(input);

// 初始化时同步
input.setAttribute('value', 'initial');
console.log(input.value);  // "initial"

// 模拟用户输入
input.value = 'user typed';

console.log(input.value);  // "user typed"
console.log(input.getAttribute('value'));  // "initial"
```

你愣住了。用户输入后,property更新了,但attribute还停留在初始值。

下午五点,测试同事又路过你的工位:"搞定了没?我要准备测试报告了。"

"快了,"你头也不抬,"再给我半小时。"

你试着修改attribute,看看会发生什么:

```javascript
input.setAttribute('value', 'new default');
console.log(input.value);  // "user typed"
console.log(input.defaultValue);  // "new default"
```

当前值没变,但有个叫`defaultValue`的property更新了。"原来attribute存的是默认值,"你突然明白了,"property存的是当前值!"

你快速测试了不同类型的属性:

```javascript
// 布尔值:存在即为true
input.setAttribute('disabled', '');
console.log(input.disabled);  // true

input.disabled = false;
console.log(input.getAttribute('disabled'));  // null

// 名称不一致的情况
const div2 = document.createElement('div');
div2.setAttribute('class', 'container');
console.log(div2.className);  // "container"
```

"布尔attribute的存在就代表true,"你记录下来,"而且有些property和attribute名字不一样,比如`class`对应`className`..."

下午五点半,产品经理又发来消息:"怎么样了?要不要延期到明天?"

你快速回复:"不用,马上修好。"你终于明白问题在哪里了。

---

## 真相浮现

你打开之前写的代码,看着那行错误的实现:

```javascript
// ❌ 错误:读取attribute获取的是初始值
const input = document.querySelector('#username');
localStorage.setItem('username', input.getAttribute('value'));

// ✅ 正确:读取property获取的是当前值
localStorage.setItem('username', input.value);
```

你快速修改代码,保存时用`input.value`,恢复时也用`input.value = savedValue`。刷新页面测试——完美!输入的内容成功保存和恢复了。

你整理了attribute和property的核心区别:

```javascript
const input = document.createElement('input');
input.type = 'text';
input.setAttribute('value', 'initial');

// 用户输入后
input.value = 'user input';

console.log('Attribute(初始值):', input.getAttribute('value'));  // "initial"
console.log('Property(当前值):', input.value);  // "user input"
```

checkbox也是同样的模式:

```javascript
const checkbox = document.createElement('input');
checkbox.type = 'checkbox';
checkbox.setAttribute('checked', '');

console.log(checkbox.checked);  // true(当前状态)
console.log(checkbox.defaultChecked);  // true(初始状态)

checkbox.checked = false;  // 用户取消勾选

console.log(checkbox.checked);  // false(当前状态)
console.log(checkbox.defaultChecked);  // true(初始状态不变)
```

你保存代码,运行测试套件——全部通过。你给产品经理发了条消息:"修好了,可以测试。"

几分钟后,产品经理回复:"测试通过!辛苦了。"

你靠在椅背上,长长地呼出一口气。窗外的雨已经停了,天边露出一抹晚霞。你看了一眼时间——下午六点整,刚好赶在下班前搞定。

---

## 世界法则

**世界规则 1: Attribute和Property是两个不同的系统**

```javascript
const div = document.createElement('div');

// Attribute: HTML标签上的文本属性
div.setAttribute('data-id', '123');
console.log(div.getAttribute('data-id'));  // "123"

// Property: JavaScript对象上的属性
div.customProp = 'value';
console.log(div.customProp);  // "value"
console.log(div.getAttribute('customProp'));  // null
```

**Attribute**: 存在于HTML,只能是字符串,用`getAttribute/setAttribute`访问
**Property**: 存在于DOM对象,可以是任何类型,用点号或方括号访问

**世界规则 2: value和checked的特殊行为**

```javascript
const input = document.createElement('input');
input.type = 'text';
input.setAttribute('value', 'initial');

// 初始时同步
console.log(input.value);  // "initial"

// 用户输入后分裂
input.value = 'user input';
console.log(input.value);                // "user input"(当前值)
console.log(input.getAttribute('value')); // "initial"(初始值)
console.log(input.defaultValue);         // "initial"(初始值的别名)
```

**规律**: attribute存储初始值,property存储当前值

**世界规则 3: 布尔attribute的特殊处理**

```javascript
const button = document.createElement('button');

// 存在即为true
button.setAttribute('disabled', '');         // true
button.setAttribute('disabled', 'false');    // 仍然是true!

// 只有移除才是false
button.removeAttribute('disabled');  // false

// property则是正常布尔值
button.disabled = true;   // true
button.disabled = false;  // false(会移除attribute)
```

**世界规则 4: Attribute和Property名称不一致**

| Attribute | Property | 原因 |
|-----------|----------|------|
| `class` | `className` | class是保留字 |
| `for` | `htmlFor` | for是保留字 |
| `readonly` | `readOnly` | 驼峰命名 |

```javascript
element.setAttribute('class', 'container');
console.log(element.className);  // "container"
```

**世界规则 5: 最佳实践**

```javascript
// ✅ 用property读取当前值
const currentValue = input.value;
const isChecked = checkbox.checked;

// ✅ 用attribute处理自定义数据
element.setAttribute('data-user-id', '123');
const userId = element.getAttribute('data-user-id');

// ✅ 用dataset快捷访问data-*
element.dataset.userId = '123';  // 等同于data-user-id
console.log(element.dataset.userId);  // "123"

// ❌ 避免用attribute读取当前值
input.getAttribute('value')  // 这是初始值,不是当前值
```

---

**事故档案编号**: DOM-2024-0808
**影响范围**: 所有涉及表单元素状态的操作
**根本原因**: 混淆attribute(初始值)和property(当前值)的概念
**修复成本**: 低(理解概念后更改API调用)

这是DOM世界第8次被记录的属性双重身份事故。HTML标签上的attribute是蓝图,DOM对象上的property是实体。蓝图记录初始设计,实体反映当前状态。混淆两者,你将永远读不到真实的数据。
