《第 120 次记录：样式操作之争 —— className 与 style 的选择困境》

## 代码审查

周二下午 2 点 30 分,技术组的会议室里,投影屏幕上显示着你的 Pull Request。

这是一个主题切换功能 —— 用户可以在亮色和暗色主题之间切换。代码不复杂,但评论区已经有了 5 条讨论。前端组的小张第一个发言:"为什么这里用 `className` 直接替换整个类名?如果元素本身还有其他类,不就丢失了吗?"

你点开代码,指向第 47 行:

```javascript
// 主题切换实现
function toggleTheme(isDark) {
  const body = document.body;
  body.className = isDark ? 'theme-dark' : 'theme-light';
}
```

"这段代码在测试环境运行正常," 你解释道,"body 元素只用来标记主题,没有其他类名。"

小张皱起眉头:"但如果将来有人给 body 加了别的类呢?比如 `loading` 或者 `modal-open`?"

设计师小李也加入讨论:"我更关心性能。这个主题切换会修改大量 CSS 变量,会不会引发重排?"

会议室陷入沉默。技术主管敲了敲桌子:"我们先把问题拆开讨论。首先,类名操作有哪些方式?"

## 方案对比

你打开一个新的 Chrome DevTools,开始现场演示。

"JavaScript 操作样式主要有三种方式," 你一边说一边输入测试代码:

```javascript
const element = document.createElement('div');

// 方式 1: 直接操作 className
element.className = 'box active';
console.log(element.className); // "box active"

// 方式 2: 使用 classList API
element.classList.add('highlight');
element.classList.remove('active');
element.classList.toggle('visible');
console.log(element.className); // "box highlight visible"

// 方式 3: 直接操作 style
element.style.color = 'red';
element.style.backgroundColor = '#f0f0f0';
```

小张点头:"我知道 `classList` 更安全,但为什么?"

你调出一个对比示例:

```javascript
// 场景:元素有多个类名
const button = document.querySelector('.btn');
button.className = 'btn primary active';

// ❌ 使用 className 添加新类
button.className = button.className + ' loading';
console.log(button.className); // "btn primary active loading"

// 但如果想移除 'active'?
button.className = button.className.replace('active', '');
console.log(button.className); // "btn primary  loading" - 注意两个空格!

// ✅ 使用 classList
button.classList.remove('active');
button.classList.add('disabled');
console.log(button.className); // "btn primary loading disabled"
```

小李在旁边补充:"而且 `classList` 方法不会触发不必要的重排。"

"这个说法不太准确," 技术主管插话,"修改类名本身就会触发重排,关键是你触发了几次。"

你立刻写了个性能测试:

```javascript
// 性能测试:批量操作 100 个元素

// 测试 1: 使用 className
console.time('className');
const elements1 = document.querySelectorAll('.test-1');
elements1.forEach(el => {
  el.className = el.className.replace('old', 'new');
});
console.timeEnd('className');
// className: 2.3ms

// 测试 2: 使用 classList
console.time('classList');
const elements2 = document.querySelectorAll('.test-2');
elements2.forEach(el => {
  el.classList.remove('old');
  el.classList.add('new');
});
console.timeEnd('classList');
// classList: 2.1ms
```

"性能差异不大," 小张若有所思,"那 `classList` 的优势主要是代码可读性?"

"还有安全性," 你强调,"看这个陷阱:"

```javascript
const element = document.createElement('div');
element.className = 'container active';

// 想要切换 'active' 状态
// ❌ 错误做法
if (element.className.includes('active')) {
  element.className = element.className.replace('active', '');
} else {
  element.className += ' active';
}

// 问题 1: 'active-tab' 也会匹配到 'active'
// 问题 2: 移除后可能留下多余空格
// 问题 3: 添加前没检查是否已存在

// ✅ 正确做法
element.classList.toggle('active');
```

## 深度对比

技术主管投影了一个复杂场景:"那么,什么时候用 `className`,什么时候用 `classList`,什么时候直接操作 `style`?"

你思考了片刻,画了一个决策树:

```javascript
// 场景 1: 完全替换所有类名
const modal = document.createElement('div');
modal.className = 'modal modal-large modal-centered';
// 适用:初始化、重置状态

// 场景 2: 增删改单个类
const button = document.querySelector('.btn');
button.classList.add('loading');      // 添加
button.classList.remove('disabled');  // 移除
button.classList.toggle('active');    // 切换
button.classList.replace('old', 'new'); // 替换
// 适用:状态切换、交互反馈

// 场景 3: 动态样式(非预定义)
const box = document.createElement('div');
box.style.width = `${userInput}px`;
box.style.transform = `rotate(${angle}deg)`;
// 适用:动画、用户自定义样式

// 场景 4: 批量样式修改
const panel = document.querySelector('.panel');
panel.style.cssText = `
  display: flex;
  flex-direction: column;
  gap: 10px;
`;
// 适用:批量设置、内联覆盖
```

小李问:"那我们的主题切换应该用哪种方式?"

"用 CSS 变量最好," 你打开一个新的示例:

```javascript
// ❌ 方案 1: 逐个修改 style(最慢)
function setDarkTheme() {
  document.body.style.backgroundColor = '#1a1a1a';
  document.body.style.color = '#ffffff';
  // ...50 个属性
}

// ❌ 方案 2: 修改每个元素的 class(较慢)
function setDarkTheme() {
  document.querySelectorAll('.card').forEach(el => {
    el.classList.add('card-dark');
  });
  // ...10 种元素类型
}

// ✅ 方案 3: 修改根元素 class + CSS 变量(最快)
function setDarkTheme() {
  document.body.classList.add('theme-dark');
  document.body.classList.remove('theme-light');
}

// CSS:
// :root {
//   --bg-color: #ffffff;
//   --text-color: #000000;
// }
//
// .theme-dark {
//   --bg-color: #1a1a1a;
//   --text-color: #ffffff;
// }
//
// .card {
//   background: var(--bg-color);
//   color: var(--text-color);
// }
```

"只需要修改一个元素的类名," 小张恍然大悟,"CSS 变量会自动传播到所有子元素。"

技术主管补充:"这就是 CSS 自定义属性的威力。但也要注意 `style` 的优先级陷阱:"

```javascript
// HTML:
// <div class="box" style="color: red;">文本</div>

const box = document.querySelector('.box');

// CSS:
// .box { color: blue !important; }

// JavaScript 修改
box.style.color = 'green';

// 实际渲染结果?
// 优先级: inline style (1000) < !important (10000)
// 所以文本仍然是 blue!

// 要覆盖 !important,必须用:
box.style.setProperty('color', 'green', 'important');
```

## 最佳实践

会议进入尾声,你重构了主题切换的代码:

```javascript
// 最终方案:结合 classList 和 CSS 变量
class ThemeManager {
  constructor() {
    this.root = document.documentElement;
    this.currentTheme = 'light';
  }

  setTheme(themeName) {
    // 移除旧主题类
    this.root.classList.remove(`theme-${this.currentTheme}`);

    // 添加新主题类
    this.root.classList.add(`theme-${themeName}`);

    // 更新状态
    this.currentTheme = themeName;

    // 可选:保存到 localStorage
    localStorage.setItem('theme', themeName);
  }

  toggleTheme() {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }

  // 安全的样式修改:批量操作
  updateCustomProperties(properties) {
    Object.entries(properties).forEach(([key, value]) => {
      this.root.style.setProperty(key, value);
    });
  }
}

// 使用
const theme = new ThemeManager();
theme.setTheme('dark');

// 自定义颜色
theme.updateCustomProperties({
  '--primary-color': '#007bff',
  '--secondary-color': '#6c757d'
});
```

小张看着新代码点头:"这样确实清晰多了。`classList` 处理状态切换,`style.setProperty` 处理动态值。"

"还有一个性能细节," 你补充道,"如果要修改多个样式,用 `cssText` 更快:"

```javascript
// ❌ 逐个修改(触发多次重排)
element.style.width = '100px';
element.style.height = '100px';
element.style.backgroundColor = 'red';

// ✅ 批量修改(触发一次重排)
element.style.cssText = 'width: 100px; height: 100px; background-color: red;';

// ✅ 或者使用对象形式
element.style.cssText = Object.entries({
  width: '100px',
  height: '100px',
  backgroundColor: 'red'
}).map(([key, value]) => {
  // 转换驼峰到短横线
  const cssKey = key.replace(/([A-Z])/g, '-$1').toLowerCase();
  return `${cssKey}: ${value}`;
}).join('; ');
```

技术主管在白板上总结:

```
样式操作决策树:

1. 需要完全替换类名? → className
2. 需要增删单个类? → classList
3. 需要动态计算样式? → style.property
4. 需要批量修改样式? → style.cssText
5. 需要主题切换? → classList + CSS 变量
6. 需要覆盖 !important? → style.setProperty(name, value, 'important')
```

小李问最后一个问题:"那 `element.getAttribute('class')` 和 `element.className` 有什么区别?"

你立刻写了个对比:

```javascript
const div = document.createElement('div');
div.className = 'box active';

console.log(div.className);           // "box active" (DOMString)
console.log(div.getAttribute('class')); // "box active" (字符串)
console.log(div.classList);           // DOMTokenList(2) ["box", "active"]

// 区别:
// className 是 Property,读写更快
// getAttribute 是 Attribute,读取 HTML 原始值
// classList 是 DOMTokenList,提供数组方法

// 对于 class,推荐优先级:
// classList > className > getAttribute
```

下午 4 点,Code Review 结束。小张在评论区回复:"LGTM(Looks Good To Me),学到了!"

你的 Pull Request 被合并了。

## 样式操作法则

**规则 1: classList 优于 className 的三个理由**

`classList` 提供了更安全的类名操作方式。第一,它不会意外覆盖其他类名;第二,它自动处理重复添加和空格问题;第三,`toggle()` 方法提供了原子性的状态切换。而 `className` 适用于完全替换类名的场景,比如组件初始化。

```javascript
// classList 的四个核心方法
element.classList.add('class1', 'class2');    // 添加(可多个)
element.classList.remove('class1');           // 移除
element.classList.toggle('active');           // 切换
element.classList.replace('old', 'new');      // 替换
element.classList.contains('active');         // 检查

// 高级用法
element.classList.toggle('visible', condition); // 条件切换
Array.from(element.classList);                 // 转数组
```

**规则 2: 直接操作 style 只适用于动态值**

`style` 属性应该只用于运行时计算的样式,而不是预定义的状态。原因有三:第一,内联样式优先级高(1000),难以覆盖;第二,样式和逻辑混在一起不利于维护;第三,无法利用 CSS 的媒体查询和伪类。

```javascript
// ✅ 适合用 style 的场景:动态计算
element.style.width = `${data.width}px`;
element.style.transform = `translate(${x}px, ${y}px)`;
element.style.setProperty('--dynamic-color', userColor);

// ❌ 不适合用 style 的场景:固定状态
element.style.display = 'none';  // 应该用 class + CSS
element.style.color = 'red';     // 应该用 class + CSS
```

**规则 3: cssText 用于批量修改以减少重排**

多次修改 `style` 的单个属性会触发多次重排。使用 `cssText` 可以一次性设置多个样式,只触发一次重排。但要注意,`cssText` 会覆盖所有内联样式。

```javascript
// 性能对比
// ❌ 触发 3 次重排
element.style.width = '100px';
element.style.height = '100px';
element.style.backgroundColor = 'red';

// ✅ 触发 1 次重排
element.style.cssText = 'width: 100px; height: 100px; background-color: red;';

// ⚠️ 注意:cssText 会覆盖之前的所有内联样式
element.style.color = 'blue';
element.style.cssText = 'width: 100px;';
console.log(element.style.color); // "" - 被清空了!
```

**规则 4: CSS 变量 + classList 实现高性能主题切换**

通过在根元素切换类名 + CSS 自定义属性,可以用最小的 DOM 操作实现全局主题切换。关键原理:CSS 变量会继承,修改根元素的变量会自动影响所有子元素。

```javascript
// 高性能主题切换方案
document.documentElement.classList.toggle('dark-theme');

// CSS 定义
// :root {
//   --bg: #fff;
//   --text: #000;
// }
// .dark-theme {
//   --bg: #1a1a1a;
//   --text: #fff;
// }
// body {
//   background: var(--bg);
//   color: var(--text);
// }

// 优势:
// 1. 只修改一个元素的 class
// 2. 浏览器自动传播变量
// 3. 支持 CSS 过渡动画
```

**规则 5: style.setProperty 覆盖 !important**

普通的 `style.property = value` 无法覆盖 CSS 中的 `!important` 规则。必须使用 `setProperty` 方法并传入第三个参数 `'important'`。

```javascript
// CSS: .box { color: blue !important; }

const box = document.querySelector('.box');

// ❌ 无效:无法覆盖 !important
box.style.color = 'red';
console.log(box.style.color); // "red" (已设置)
// 但渲染结果仍是 blue

// ✅ 有效:覆盖 !important
box.style.setProperty('color', 'red', 'important');
// 渲染结果变成 red

// 检查是否有 important
console.log(box.style.getPropertyPriority('color')); // "important"

// 移除 important
box.style.setProperty('color', 'red', '');
```

**规则 6: className vs getAttribute('class') 的性能差异**

`className` 是 DOM Property,直接访问 JavaScript 对象属性,性能更高。`getAttribute('class')` 需要读取 HTML Attribute,有额外的序列化开销。除非需要读取 HTML 原始值,否则优先使用 `className` 或 `classList`。

```javascript
// 性能对比(100000 次读取)
const element = document.createElement('div');
element.className = 'box active highlight';

console.time('className');
for (let i = 0; i < 100000; i++) {
  const cls = element.className;
}
console.timeEnd('className'); // ~2ms

console.time('getAttribute');
for (let i = 0; i < 100000; i++) {
  const cls = element.getAttribute('class');
}
console.timeEnd('getAttribute'); // ~15ms

// className 快 7 倍
// 推荐优先级: classList > className > getAttribute
```

---

**记录者注**:

样式操作不是简单的"改个类名"或"设个颜色"。`className` 是字符串操作,简单但危险;`classList` 是对象 API,安全但稍慢;`style` 是内联样式,强大但优先级高。

选择哪种方式,取决于你的场景:状态切换用 `classList`,动态计算用 `style`,主题系统用 CSS 变量。记住:**能用 CSS 解决的,不要用 JavaScript;能用 classList 解决的,不要用 className;能用类名解决的,不要用内联样式**。

理解这些原则,才能写出既高性能又易维护的样式操作代码。
