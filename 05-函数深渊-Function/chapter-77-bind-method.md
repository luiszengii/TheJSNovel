《第77次记录：bind —— this的永久契约》

---

## 事件bug

周四上午十点，刚接手React项目的实习生小王急匆匆跑过来："按钮点击报错了，但代码看起来没问题啊！"

你走到他的工位，看到控制台的错误：

```
TypeError: Cannot read property 'setState' of undefined
    at handleClick (App.js:12)
```

"让我看看代码。"你打开`App.js`：

```javascript
class Counter extends React.Component {
    constructor(props) {
        super(props);
        this.state = { count: 0 };
    }

    handleClick() {
        this.setState({ count: this.state.count + 1 });
    }

    render() {
        return (
            <button onClick={this.handleClick}>
                点击: {this.state.count}
            </button>
        );
    }
}
```

"代码看起来确实没问题，"小王委屈地说，"为什么`this`会是`undefined`？"

"经典的this丢失问题，"你笑了笑，"事件处理器调用时，this没有正确绑定。"

---

## this丢失

你给小王解释："当你把`this.handleClick`作为回调传递时，方法和对象分离了，this就丢失了。"

```javascript
// 简化示例
const obj = {
    name: 'Alice',
    greet() {
        console.log(this.name);
    }
};

obj.greet(); // "Alice" - this指向obj

const greet = obj.greet; // 提取方法
greet(); // undefined - this丢失
```

"React的onClick接收的是函数引用，调用时this已经不是组件实例了。"你继续说，"有几种解决方案，最常用的是`bind`。"

---

## bind绑定

你修改了小王的代码：

```javascript
class Counter extends React.Component {
    constructor(props) {
        super(props);
        this.state = { count: 0 };
        // 在constructor中bind
        this.handleClick = this.handleClick.bind(this);
    }

    handleClick() {
        this.setState({ count: this.state.count + 1 });
    }

    render() {
        return <button onClick={this.handleClick}>点击: {this.state.count}</button>;
    }
}
```

"成功了！"小王看着能正常工作的按钮，"但`bind`到底做了什么？"

"bind创建了一个新函数，this永久绑定到指定对象，"你解释，"看这个例子：

```javascript
function greet() {
    console.log(`Hello, ${this.name}`);
}

const person = { name: 'Alice' };

// bind返回新函数，this永久绑定到person
const boundGreet = greet.bind(person);

boundGreet(); // "Hello, Alice"

// 即使用call/apply也无法改变
const another = { name: 'Bob' };
boundGreet.call(another); // 依然是 "Hello, Alice"
```

"bind还支持预设参数，"你又写了个例子：

```javascript
function multiply(a, b) {
    return a * b;
}

// 预设第一个参数为2
const double = multiply.bind(null, 2);

double(5); // 10 (相当于 multiply(2, 5))
double(10); // 20 (相当于 multiply(2, 10))
```

小王恍然大悟："所以bind既能绑定this，又能预设参数！"

---

## 绑定策略

你给小王列出了React中处理this的几种方案：

```javascript
class Example extends React.Component {
    // 方案1: constructor中bind（推荐）
    constructor(props) {
        super(props);
        this.method1 = this.method1.bind(this);
    }
    method1() { }

    // 方案2: render中bind（不推荐，每次render都创建新函数）
    render() {
        return <button onClick={this.method2.bind(this)} />;
    }
    method2() { }

    // 方案3: 箭头函数属性（推荐）
    method3 = () => {
        // 箭头函数自动绑定this
    }

    // 方案4: render中箭头函数（不推荐，每次render创建新函数）
    render() {
        return <button onClick={() => this.method4()} />;
    }
    method4() { }
}
```

"方案1和3最常用，"你总结，"方案2和4会在每次render时创建新函数，影响性能。"

小王又问："那bind有什么限制吗？"

"最大的限制是bind返回的函数无法再次改变this，"你回答，"而且会丢失原函数的name：

```javascript
function original() { }
console.log(original.name); // "original"

const bound = original.bind(null);
console.log(bound.name); // "bound original"
```

---

## bind知识总结

**规则 1: bind基础**

```javascript
const newFunc = func.bind(thisArg, arg1, arg2, ...);

// thisArg: 绑定的this值
// arg1, arg2: 预设的参数
// 返回: 新函数（原函数不变）
```

---

**规则 2: this永久绑定**

```javascript
const obj = { name: 'Alice' };

function greet() {
    return this.name;
}

const bound = greet.bind(obj);

bound(); // "Alice"
bound.call({ name: 'Bob' }); // 依然是 "Alice"（无法改变）
```

---

**规则 3: 偏函数应用**

```javascript
function add(a, b, c) {
    return a + b + c;
}

const add5 = add.bind(null, 5); // 预设a=5
add5(10, 20); // 35 (5+10+20)

const add5and10 = add.bind(null, 5, 10); // 预设a=5, b=10
add5and10(20); // 35 (5+10+20)
```

---

**规则 4: 事件处理器**

```javascript
class Button {
    constructor() {
        this.count = 0;
        // constructor中bind
        this.handleClick = this.handleClick.bind(this);
    }

    handleClick() {
        this.count++;
    }
}
```

---

**规则 5: bind vs 箭头函数**

```javascript
class Component {
    // bind方式
    constructor() {
        this.method1 = this.method1.bind(this);
    }
    method1() { }

    // 箭头函数方式（更简洁）
    method2 = () => { }
}
```

---

**规则 6: 使用建议**

- 事件处理器：优先使用箭头函数属性
- 需要预设参数：使用bind的偏函数特性
- 避免在render中bind（性能问题）
- 不能bind箭头函数（箭头函数无this）

---

**事故档案编号**: FUNC-2024-1877
**影响范围**: this绑定,事件处理,React开发
**根本原因**: 不理解方法传递时this丢失,未正确绑定this
**修复成本**: 低(添加bind或使用箭头函数)

这是JavaScript世界第77次被记录的this绑定事故。`bind`方法创建新函数,永久绑定this值,并支持预设参数(偏函数应用)。与call/apply的临时绑定不同,bind的绑定无法被call/apply覆盖。主要用途:事件处理器this绑定、创建偏函数、方法提取保持this。现代JavaScript中,箭头函数属性提供了更简洁的this绑定方案,但bind在需要预设参数时仍不可替代。

---
