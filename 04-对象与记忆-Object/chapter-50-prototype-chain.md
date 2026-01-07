《第50次记录: 原型链迷宫 —— 神秘消失的方法》

---

## 困惑时刻

周一上午十点, 阳光透过办公室的落地窗洒在你的键盘上。你端着咖啡, 准备开始新一周的工作。

"老王!"实习生小林急匆匆地跑过来, 脸上写满了困惑,"我按照你上周教的方式扩展了第三方库, 但方法调用不了, 一直报`is not a function`错误。代码明明是对的啊!"

你放下咖啡杯, 示意他把代码给你看。小林打开他的编辑器, 指着屏幕:"你看, 我想给第三方的`DataProcessor`库增加一个`validate`方法, 就像你说的, 用原型继承..."

你看了看代码, 眉头微微皱起。代码确实是按照经典的继承模式写的, 但总感觉哪里不对劲。

"先别急, 我们一起看看。"你说着, 把小林的代码拷贝到自己的电脑上。

这时, 团队负责人老张走过来:"小林的任务卡住了? 这个功能今天下午要演示给产品部门的, 他们等着看新的数据验证功能呢。"

你心里一紧。产品部门的会议是下午三点, 现在是上午十点, 只有五个小时。

"放心, 我们马上搞定。"你对老张说, 但手心已经开始微微出汗。你知道继承和原型链是JavaScript最容易出错的地方, 如果搞不清楚原理, 可能会陷入无尽的调试循环。

小林在旁边焦虑地说:"我昨天调试了三个小时, 试了好几种写法, 都不行。最奇怪的是, 有些方法能调用, 有些就不行, 就像走进了迷宫一样..."

你让小林先回去喝杯水冷静一下, 自己开始仔细分析代码。你打开Chrome DevTools, 在控制台里输入对象, 查看它的属性和方法。

第一眼看上去, 对象确实有`validate`方法。但当你尝试调用时, 却报错:`TypeError: processor. validate is not a function`。

"怎么会这样?"你盯着屏幕, 手指敲击着桌面,"明明能看到方法, 为什么调用不了?"

你深吸一口气, 决定从头梳理继承链。你知道, 原型链就像一个迷宫, 如果不理解它的运作机制, 很容易在里面迷路, 找不到出口。

窗外的阳光逐渐变得刺眼, 你调暗了显示器亮度, 开始了这场与原型链的较量。

---

## 同事点拨

上午十点半, 你打开了小林的代码。这是一个典型的继承场景:

```javascript
// 第三方库 (不能修改)
function DataProcessor(data) {
    this. data = data;
}

DataProcessor. prototype. process = function() {
    return this. data. map(item => item * 2);
};

// 小林的扩展
function ValidatedProcessor(data) {
    DataProcessor. call(this, data);
}

ValidatedProcessor. prototype. validate = function() {
    return this. data. every(item => typeof item === 'number');
};
```

你看着代码, 皱起眉头。"等等, 小林只给`ValidatedProcessor`的原型添加了`validate`方法, 但他有继承`DataProcessor`的`process`方法吗?"

你在控制台测试:

```javascript
const processor = new ValidatedProcessor([1, 2, 3]);
console. log(processor. validate); // function - 有!
console. log(processor. process);  // undefined - 没有!
```

"果然!"你恍然大悟,"小林忘记建立原型链了。`ValidatedProcessor`的原型并没有连接到`DataProcessor`的原型, 所以继承不到`process`方法!"

这时小林端着水杯回来了:"怎么样, 找到原因了吗?"

"找到了一部分。"你说,"你创建了`ValidatedProcessor`, 也添加了`validate`方法, 但你没有把它和`DataProcessor`连接起来。现在你的对象只能用`validate`, 不能用`process`。"

小林挠了挠头:"可是我用了`call`啊, 不是已经调用了`DataProcessor`的构造函数吗?"

"那只是借用了构造函数, 初始化了`this. data`, 但原型链没有建立。"你耐心解释,"你需要让`ValidatedProcessor. prototype`继承自`DataProcessor. prototype`。"

你快速写下修复代码:

```javascript
function ValidatedProcessor(data) {
    DataProcessor. call(this, data); // 借用构造函数
}

// 建立原型链!
ValidatedProcessor. prototype = Object. create(DataProcessor. prototype);
ValidatedProcessor. prototype. constructor = ValidatedProcessor;

// 现在可以添加新方法
ValidatedProcessor. prototype. validate = function() {
    return this. data. every(item => typeof item === 'number');
};
```

"试试看。"你说。

小林复制代码, 刷新页面, 在控制台输入:

```javascript
const processor = new ValidatedProcessor([1, 2, 3]);
processor. validate(); // true - 成功!
processor. process();  // [2, 4, 6] - 也成功了!
```

"成功了!"小林兴奋地说,"但为什么`Object. create`就能建立原型链呢?"

你看了看时间, 上午十一点, 还有四个小时。你决定花十分钟给小林解释清楚原理, 这样他以后就不会再犯错了。

"来, 我画个图给你看。"你打开白板, 开始画原型链的关系图。

你一边画一边解释:"每个对象都有一个内部属性`[[Prototype]]`, 指向它的原型对象。当你访问一个属性或方法时, JavaScript引擎会先在对象自身查找, 如果没有, 就沿着原型链向上查找, 直到找到或到达`null`为止。"

小林若有所思地点头:"所以`Object. create(DataProcessor. prototype)`是创建了一个新对象, 它的`[[Prototype]]`指向`DataProcessor. prototype`?"

"对!"你赞许地说,"这样`ValidatedProcessor. prototype`就继承了`DataProcessor. prototype`的所有方法。当你创建`new ValidatedProcessor([1, 2, 3])`时, 这个实例的`[[Prototype]]`指向`ValidatedProcessor. prototype`, 而`ValidatedProcessor. prototype`的`[[Prototype]]`又指向`DataProcessor. prototype`, 形成了一条链。"

小林恍然大悟:"所以调用`processor. process()`时, JavaScript先在`processor`自身找, 没有, 再去`ValidatedProcessor. prototype`找, 还是没有, 再去`DataProcessor. prototype`找, 找到了!"

"完全正确!"你拍了拍小林的肩膀。

这时, 老张又走过来:"搞定了? 我看你们聊得挺开心。"

"搞定了。"你说,"小林现在理解原型链了, 不会再掉进这个坑里。"

但你的心里还有些不安。你想起小林说的"有些方法能调用, 有些不行", 说明还有其他问题。你仔细看了看小林完整的代码...

突然, 你发现了另一个问题。

---

## 豁然开朗

中午十二点, 你和小林一起整理了完整的原型继承方案。你在白板上写下错误和正确的对比:

**❌ 错误1: 忘记建立原型链**

小林最初的代码问题就在这里——只借用了构造函数, 没有继承原型:

```javascript
function ValidatedProcessor(data) {
    DataProcessor. call(this, data); // 只借用构造函数
}
// 缺少原型链连接!

ValidatedProcessor. prototype. validate = function() {
    return this. data. every(item => typeof item === 'number');
};

const p = new ValidatedProcessor([1, 2, 3]);
p. process(); // TypeError: process is not a function
```

**✅ 正确: 完整的继承流程**

你给小林演示了正确的继承三步骤:

```javascript
// 步骤1: 借用构造函数(继承实例属性)
function ValidatedProcessor(data) {
    DataProcessor. call(this, data);
}

// 步骤2: 建立原型链(继承原型方法)
ValidatedProcessor. prototype = Object. create(DataProcessor. prototype);

// 步骤3: 修复constructor指向
ValidatedProcessor. prototype. constructor = ValidatedProcessor;

// 步骤4: 添加子类方法
ValidatedProcessor. prototype. validate = function() {
    return this. data. every(item => typeof item === 'number');
};
```

小林指着第三步问:"为什么要修复`constructor`? 不修复会怎样?"

你解释道:"如果不修复,`ValidatedProcessor. prototype. constructor`会指向`DataProcessor`, 虽然不影响功能, 但会造成概念混淆。比如你想判断对象的类型时, 会得到错误的结果。"

你在控制台演示:

```javascript
// 没修复constructor的情况
const p1 = new ValidatedProcessor([1, 2, 3]);
p1. constructor === ValidatedProcessor; // false!
p1. constructor === DataProcessor;      // true - 错误!

// 修复后
ValidatedProcessor. prototype. constructor = ValidatedProcessor;
const p2 = new ValidatedProcessor([1, 2, 3]);
p2. constructor === ValidatedProcessor; // true - 正确!
```

**❌ 错误2: 直接赋值原型对象**

你还发现小林尝试过另一种错误写法:

```javascript
// 错误! 这样会覆盖原型
ValidatedProcessor. prototype = DataProcessor. prototype;

ValidatedProcessor. prototype. validate = function() {
    return this. data. every(item => typeof item === 'number');
};

// 问题: DataProcessor也有了validate方法!
const base = new DataProcessor([1, 2, 3]);
base. validate(); // 意外地可以调用!
```

"看到了吗?"你指着屏幕,"直接赋值会让两个类共享同一个原型对象, 你给子类添加方法, 父类也会受影响!"

小林倒吸一口凉气:"天哪, 我之前就是这么写的! 还好测试发现了问题。"

下午两点, 你们完成了所有代码的修复和测试。小林的数据验证功能完美运行, 既能使用父类的`process`方法, 又有自己的`validate`方法。

下午三点, 产品部门的演示会议上, 小林成功展示了新功能。会后, 老张走过来:"干得不错, 小林进步很快。老王, 谢谢你的指导。"

你笑了笑:"没什么, 理解了原型链, JavaScript就不难了。"

---

## 原型机制

**规则 1: 原型链的查找机制**

当访问对象的属性或方法时, JavaScript引擎按以下顺序查找:

```javascript
const obj = new ValidatedProcessor([1, 2, 3]);
obj. validate();

// 查找顺序:
// 1. obj自身 → 没有validate
// 2. obj.[[Prototype]] (即ValidatedProcessor. prototype) → 找到validate!
// 3. 如果没找到, 继续向上查找DataProcessor. prototype
// 4. 如果还没找到, 继续查找Object. prototype
// 5. 如果还没找到, 查找null, 返回undefined
```

原型链的终点是`null`。

---

**规则 2: 实现继承的三步骤**

```javascript
// 步骤1: 借用构造函数(继承实例属性)
function Child(value) {
    Parent. call(this, value);
}

// 步骤2: 建立原型链(继承方法)
Child. prototype = Object. create(Parent. prototype);

// 步骤3: 修复constructor
Child. prototype. constructor = Child;
```

缺少任何一步都会导致继承不完整。

---

**规则 3: Object. create的作用**

```javascript
// Object. create(proto) 创建一个新对象, 其[[Prototype]]指向proto

const parent = { name: 'parent' };
const child = Object. create(parent);

child. age = 10;

console. log(child. age);  // 10 - 自身属性
console. log(child. name); // 'parent' - 从原型继承

// 原型链: child → parent → Object. prototype → null
```

这比直接赋值原型更安全, 不会污染父类。

---

**规则 4: constructor属性的重要性**

```javascript
function MyClass() {}
const obj = new MyClass();

// constructor指向构造函数
obj. constructor === MyClass; // true

// 用途1: 判断对象类型
if (obj. constructor === MyClass) {
    console. log('这是MyClass的实例');
}

// 用途2: 创建同类型对象
const another = new obj. constructor();
```

修复constructor确保类型判断正确。

---

**规则 5: ES6 class语法糖**

```javascript
// ES6的class实际上也是原型继承
class DataProcessor {
    constructor(data) {
        this. data = data;
    }

    process() {
        return this. data. map(x => x * 2);
    }
}

class ValidatedProcessor extends DataProcessor {
    constructor(data) {
        super(data); // 相当于DataProcessor. call(this, data)
    }

    validate() {
        return this. data. every(x => typeof x === 'number');
    }
}

// 等价于之前的原型继承, 但更简洁
```

class是语法糖, 本质仍是原型继承。

---

**规则 6:__proto__ vs prototype**

```javascript
function MyClass() {}
const obj = new MyClass();

// prototype: 构造函数的属性, 指向原型对象
MyClass. prototype; // { constructor: MyClass }

// __proto__: 对象的内部属性, 指向它的原型
obj.__proto__ === MyClass. prototype; // true

// 注意:__proto__已废弃, 应使用Object. getPrototypeOf
Object. getPrototypeOf(obj) === MyClass. prototype; // true
```

`prototype`是函数的属性,`__proto__`是对象的内部原型引用。

---

**事故档案编号**: OBJ-2024-1750
**影响范围**: 第三方库扩展, 所有继承实现
**根本原因**: 不理解原型链的建立机制, 只借用构造函数而未连接原型
**修复成本**: 低(理解原型链后, 三行代码即可修复)

这是JavaScript世界第50次被记录的原型链事故。原型链是JavaScript继承的核心机制, 实现继承需要三步: 借用构造函数继承实例属性, 使用`Object. create`建立原型链继承方法, 修复`constructor`指向。直接赋值原型会造成污染, 忘记连接原型链会导致方法丢失。理解原型链的查找机制, 就能走出JavaScript继承的迷宫。

---
