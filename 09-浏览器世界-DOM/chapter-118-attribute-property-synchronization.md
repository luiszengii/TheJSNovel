《第 118 次记录：同步的边界 —— Attribute 与 Property 的隐秘联系》

## 实验室的发现

周六上午，你在家里写一个表单组件库。

上周的 Code Review 让你对 Attribute 和 Property 有了基本认识，但你想深入了解它们之间的同步机制 —— 到底哪些属性会同步？同步是双向的吗？有没有例外情况？

你打开一个空白 HTML 文件，开始系统地实验：

```html
<!DOCTYPE html>
<html>
<body>
  <input type="text" id="test" value="初始值" class="input">
  <script>
    const input = document.getElementById('test');

    // 实验 1: value 的单向同步
    console.log('=== 实验 1: value 属性 ===');
    console.log('初始 Attribute:', input.getAttribute('value')); // "初始值"
    console.log('初始 Property:', input.value);                   // "初始值"

    // 修改 Property
    input.value = 'Property 修改';
    console.log('修改 Property 后:');
    console.log('Attribute:', input.getAttribute('value')); // "初始值" - 没变！
    console.log('Property:', input.value);                   // "Property 修改"

    // 修改 Attribute
    input.setAttribute('value', 'Attribute 修改');
    console.log('修改 Attribute 后:');
    console.log('Attribute:', input.getAttribute('value')); // "Attribute 修改"
    console.log('Property:', input.value);                   // "Attribute 修改" - 变了！
  </script>
</body>
</html>
```

你运行这段代码，控制台输出：

```
=== 实验 1: value 属性 ===
初始 Attribute: 初始值
初始 Property: 初始值
修改 Property 后:
Attribute: 初始值
Property: Property 修改
修改 Attribute 后:
Attribute: Attribute 修改
Property: Attribute 修改
```

"有意思，" 你皱起眉头，"修改 Property 不会影响 Attribute，但修改 Attribute 会影响 Property。这是单向同步。"

但你马上发现了一个奇怪的现象：

```javascript
// 继续实验
input.setAttribute('value', '第一次修改');
console.log('第一次 setAttribute:', input.value); // "第一次修改"

input.value = '用户输入';
console.log('用户输入后:', input.value); // "用户输入"

input.setAttribute('value', '第二次修改');
console.log('第二次 setAttribute:', input.value); // "用户输入" - 没变！
```

"等等，" 你自言自语，"第二次调用 `setAttribute` 为什么不起作用了？"

你打开 Chrome DevTools，设置断点，单步调试。你发现：**一旦 `value` Property 被程序修改过（不是用户输入），Attribute 到 Property 的同步就断开了。**

"这是一个状态机，" 你在笔记里写道，"输入框有两个状态：'pristine'（未修改）和 'dirty'（已修改）。"

## 深入探索

你决定测试所有常见属性的同步行为：

```javascript
// 测试框架
function testSync(element, attrName, propName, testValue1, testValue2) {
  console.log(`\n=== 测试 ${attrName} ===`);

  // 测试 1: Attribute → Property
  element.setAttribute(attrName, testValue1);
  const propAfterAttr = element[propName];
  console.log(`setAttribute("${testValue1}") → ${propName}: ${propAfterAttr}`);

  // 测试 2: Property → Attribute
  element[propName] = testValue2;
  const attrAfterProp = element.getAttribute(attrName);
  console.log(`${propName} = "${testValue2}" → getAttribute: ${attrAfterProp}`);

  // 判断同步类型
  const attrToprop = (propAfterAttr === testValue1);
  const propToAttr = (attrAfterProp === testValue2);

  if (attrToprop && propToAttr) {
    console.log('✅ 双向同步');
  } else if (attrToprop && !propToAttr) {
    console.log('⬆️ 单向同步（Attribute → Property）');
  } else if (!attrToprop && propToAttr) {
    console.log('⬇️ 单向同步（Property → Attribute）');
  } else {
    console.log('❌ 不同步');
  }
}

// 创建测试元素
const input = document.createElement('input');
input.type = 'text';

// 测试各种属性
testSync(input, 'id', 'id', 'test-id', 'new-id');
testSync(input, 'class', 'className', 'btn primary', 'btn secondary');
testSync(input, 'title', 'title', 'Title 1', 'Title 2');
testSync(input, 'placeholder', 'placeholder', 'Placeholder 1', 'Placeholder 2');
testSync(input, 'value', 'value', 'Value 1', 'Value 2');

// 测试 checked
const checkbox = document.createElement('input');
checkbox.type = 'checkbox';
testSync(checkbox, 'checked', 'checked', '', true);
```

测试结果：

```
=== 测试 id ===
setAttribute("test-id") → id: test-id
id = "new-id" → getAttribute: new-id
✅ 双向同步

=== 测试 class ===
setAttribute("btn primary") → className: btn primary
className = "btn secondary" → getAttribute: btn secondary
✅ 双向同步

=== 测试 title ===
setAttribute("Title 1") → title: Title 1
title = "Title 2" → getAttribute: Title 2
✅ 双向同步

=== 测试 placeholder ===
setAttribute("Placeholder 1") → placeholder: Placeholder 1
placeholder = "Placeholder 2" → getAttribute: Placeholder 2
✅ 双向同步

=== 测试 value ===
setAttribute("Value 1") → value: Value 1
value = "Value 2" → getAttribute: Value 1
⬆️ 单向同步（Attribute → Property）

=== 测试 checked ===
setAttribute("") → checked: true
checked = true → getAttribute: null
⬆️ 单向同步（Attribute → Property）
```

你整理出了一个完整的分类表：

| 属性类型 | 示例 | 同步方式 | 原因 |
|---------|------|---------|------|
| **标识属性** | id, name, title | ✅ 双向同步 | 不会被用户修改 |
| **样式属性** | class, style | ✅ 双向同步 | 程序完全控制 |
| **表单输入** | value, checked | ⬆️ Attr → Prop | 保留初始值，反映当前值 |
| **布尔属性** | disabled, readonly | ⬆️ Attr → Prop | 状态型属性 |
| **URL 属性** | href, src | 🔀 特殊处理 | Attr 存相对路径，Prop 存绝对路径 |

但你很快发现了一个更诡异的现象 —— URL 属性的特殊行为。

## URL 属性的秘密

你创建了一个链接元素：

```html
<a id="link" href="/about">关于我们</a>
```

```javascript
const link = document.getElementById('link');

console.log('Attribute:', link.getAttribute('href')); // "/about"
console.log('Property:', link.href);                   // "http://localhost:8080/about"
```

"什么？" 你惊讶地发现，"Attribute 存的是相对路径 `/about`，但 Property 返回的是完整的绝对 URL `http://localhost:8080/about`？"

你做了更多测试：

```javascript
// 测试各种 URL 格式
const testCases = [
  '/about',                          // 绝对路径
  'contact.html',                     // 相对路径
  '../parent.html',                   // 父目录
  'https://example.com',              // 完整 URL
  '//cdn.example.com/script.js',     // 协议相对 URL
  '#section',                         // 锚点
  '?page=2',                          // 查询参数
];

testCases.forEach(url => {
  link.setAttribute('href', url);
  console.log(`setAttribute("${url}")`);
  console.log(`  getAttribute: ${link.getAttribute('href')}`);
  console.log(`  Property:     ${link.href}`);
  console.log('');
});
```

输出：

```
setAttribute("/about")
  getAttribute: /about
  Property:     http://localhost:8080/about

setAttribute("contact.html")
  getAttribute: contact.html
  Property:     http://localhost:8080/contact.html

setAttribute("../parent.html")
  getAttribute: ../parent.html
  Property:     http://localhost:8080/parent.html

setAttribute("https://example.com")
  getAttribute: https://example.com
  Property:     https://example.com/

setAttribute("//cdn.example.com/script.js")
  getAttribute: //cdn.example.com/script.js
  Property:     http://cdn.example.com/script.js

setAttribute("#section")
  getAttribute: #section
  Property:     http://localhost:8080/#section

setAttribute("?page=2")
  getAttribute: ?page=2
  Property:     http://localhost:8080/?page=2
```

你恍然大悟："**Attribute 存储的是开发者写的原始值，Property 存储的是浏览器解析后的规范化值。**"

这对于 `img.src`、`script.src`、`link.href` 等 URL 属性都适用：

```javascript
// img.src
const img = document.createElement('img');
img.setAttribute('src', 'images/logo.png');

console.log(img.getAttribute('src')); // "images/logo.png"
console.log(img.src);                  // "http://localhost:8080/images/logo.png"

// script.src
const script = document.createElement('script');
script.setAttribute('src', '/js/app.js');

console.log(script.getAttribute('src')); // "/js/app.js"
console.log(script.src);                  // "http://localhost:8080/js/app.js"
```

"这就是为什么调试时，读取 URL 应该用 `getAttribute`，" 你在笔记里记下，"因为它保留了代码中写的原始路径，更容易看懂。"

## 边界情况与陷阱

你继续探索边界情况，发现了几个陷阱：

**陷阱 1: 布尔属性的字符串陷阱**

```javascript
const checkbox = document.createElement('input');
checkbox.type = 'checkbox';

// 设置 Attribute 为 "false"（字符串）
checkbox.setAttribute('checked', 'false');

console.log(checkbox.getAttribute('checked')); // "false"
console.log(checkbox.checked);                  // true！

// 原因：只要 Attribute 存在，不管值是什么，Property 都是 true
checkbox.setAttribute('checked', '');           // true
checkbox.setAttribute('checked', 'no');         // true
checkbox.setAttribute('checked', '0');          // true

// 只有移除 Attribute，Property 才会是 false
checkbox.removeAttribute('checked');
console.log(checkbox.checked); // false
```

**陷阱 2: 自定义属性不会自动同步**

```javascript
const div = document.createElement('div');

// 设置自定义 Attribute
div.setAttribute('custom-attr', 'value');

console.log(div.getAttribute('custom-attr')); // "value"
console.log(div.customAttr);                   // undefined

// 自定义 Attribute 不会自动创建对应的 Property
div.customAttr = 'new value';
console.log(div.getAttribute('custom-attr')); // "value" - 没变
```

**陷阱 3: style 和 class 的特殊对象**

```javascript
const div = document.createElement('div');

// style Attribute 是字符串
div.setAttribute('style', 'color: red; font-size: 16px;');
console.log(div.getAttribute('style')); // "color: red; font-size: 16px;"

// style Property 是 CSSStyleDeclaration 对象
console.log(div.style);                 // CSSStyleDeclaration {...}
console.log(div.style.color);           // "red"
console.log(div.style.fontSize);        // "16px"

// class Attribute 是字符串
div.setAttribute('class', 'btn primary');
console.log(div.getAttribute('class')); // "btn primary"

// className Property 是字符串
console.log(div.className);             // "btn primary"

// classList Property 是 DOMTokenList 对象
console.log(div.classList);             // DOMTokenList(2) ["btn", "primary"]
```

**陷阱 4: 数字属性的类型转换**

```javascript
const input = document.createElement('input');
input.type = 'number';

// Attribute 总是字符串
input.setAttribute('value', '42');
console.log(typeof input.getAttribute('value')); // "string"

// value Property 也是字符串
console.log(typeof input.value);                 // "string"

// 但 valueAsNumber Property 是数字
console.log(typeof input.valueAsNumber);         // "number"
console.log(input.valueAsNumber);                // 42
```

你整理了一份"陷阱清单"，提醒自己在开发中避免这些坑。

## 同步机制深度解析

**规则 1: 同步分为三种模式**

浏览器对 Attribute 和 Property 的同步有三种策略：

**① 双向同步（Bidirectional）**

```javascript
// 示例：id, className, title, placeholder 等
const element = document.createElement('div');

// Attribute → Property
element.setAttribute('id', 'test');
console.log(element.id); // "test"

// Property → Attribute
element.id = 'new-id';
console.log(element.getAttribute('id')); // "new-id"

// 始终保持同步
```

适用范围：
- 标识属性：id, name, title
- 样式属性：className, lang, dir
- 元数据：placeholder, alt, label

**② 单向同步（Unidirectional: Attribute → Property）**

```javascript
// 示例：value, checked, selected 等
const input = document.createElement('input');
input.type = 'text';

// Attribute → Property（首次有效）
input.setAttribute('value', '初始值');
console.log(input.value); // "初始值"

// Property → Attribute（不同步）
input.value = '新值';
console.log(input.getAttribute('value')); // "初始值" - 保留

// 再次修改 Attribute（无效，因为已被标记为 dirty）
input.setAttribute('value', '第二次修改');
console.log(input.value); // "新值" - 不变
```

适用范围：
- 表单输入：value, checked, selected
- 状态属性：disabled, readonly, required

原因：保留初始值用于表单重置，Property 反映当前用户输入。

**③ 特殊转换（Transform）**

```javascript
// 示例：href, src 等 URL 属性
const link = document.createElement('a');

// Attribute 存储原始值
link.setAttribute('href', '/about');
console.log(link.getAttribute('href')); // "/about"

// Property 存储规范化值（完整 URL）
console.log(link.href); // "http://localhost:8080/about"

// 修改 Property
link.href = 'https://example.com';
console.log(link.getAttribute('href')); // "https://example.com" - 同步
console.log(link.href);                  // "https://example.com/" - 可能添加斜杠
```

适用范围：
- URL 属性：href, src, action, formAction
- 行为：Attribute 存原始值，Property 存解析后的绝对 URL

**规则 2: value 的"脏值标记"机制**

输入框的 value 有一个内部状态标记：

```javascript
const input = document.createElement('input');

// 初始状态：pristine（未修改）
console.log('[内部状态: pristine]');

// Attribute → Property 同步有效
input.setAttribute('value', 'A');
console.log(input.value); // "A"

input.setAttribute('value', 'B');
console.log(input.value); // "B"

// 一旦 Property 被修改，标记为 dirty
input.value = 'C';
console.log('[内部状态: dirty]');

// Attribute → Property 同步失效
input.setAttribute('value', 'D');
console.log(input.value); // "C" - 不变！

// 但 Attribute 本身会更新
console.log(input.getAttribute('value')); // "D"

// defaultValue Property 始终反映 Attribute
console.log(input.defaultValue); // "D"
```

重置机制：

```javascript
const form = document.querySelector('form');
const input = form.querySelector('input');

// 用户修改了输入框
input.value = '用户输入';

// 表单重置
form.reset();

// value 恢复到 Attribute 的值（初始值）
console.log(input.value); // 恢复到 getAttribute('value') 的值
```

**规则 3: 布尔属性只看存在性，不看值**

布尔属性（disabled, checked, readonly, required 等）的特殊规则：

```javascript
const checkbox = document.createElement('input');
checkbox.type = 'checkbox';

// 这些都会让 checked 变成 true
checkbox.setAttribute('checked', '');          // true
checkbox.setAttribute('checked', 'checked');   // true
checkbox.setAttribute('checked', 'false');     // true！
checkbox.setAttribute('checked', '0');         // true！
checkbox.setAttribute('checked', 'no');        // true！

// 只有移除 Attribute 才是 false
checkbox.removeAttribute('checked');           // false

// Property 设置更直观
checkbox.checked = true;   // 添加 Attribute
checkbox.checked = false;  // 移除 Attribute
```

HTML 规范规定：

```html
<!-- 这些都表示 checked = true -->
<input type="checkbox" checked>
<input type="checkbox" checked="">
<input type="checkbox" checked="checked">
<input type="checkbox" checked="false"> <!-- 仍然是 true！ -->

<!-- 只有完全不写才是 false -->
<input type="checkbox">
```

**规则 4: URL 属性的规范化处理**

浏览器会自动解析和规范化 URL：

```javascript
const link = document.createElement('a');
link.href = '/about';

// Attribute：原始值
link.getAttribute('href'); // "/about"

// Property：完整 URL
link.href;                  // "http://localhost:8080/about"

// 分解的 Property
link.protocol;  // "http:"
link.hostname;  // "localhost"
link.port;      // "8080"
link.pathname;  // "/about"
link.search;    // ""
link.hash;      // ""

// 修改分解的 Property
link.pathname = '/contact';
console.log(link.href); // "http://localhost:8080/contact"
console.log(link.getAttribute('href')); // "/contact" - 同步了
```

**规则 5: 自定义属性需要 data-* 前缀**

HTML5 规定，自定义属性必须以 `data-` 开头：

```html
<!-- ❌ 非标准（浏览器会保留，但不推荐） -->
<div custom="value"></div>

<!-- ✅ 标准（推荐） -->
<div data-custom="value"></div>
```

```javascript
const div = document.querySelector('div');

// 自定义 Attribute 不会创建 Property
div.setAttribute('custom', 'value');
console.log(div.custom); // undefined

// data-* 有专门的 dataset API
div.setAttribute('data-user-id', '1001');
console.log(div.dataset.userId); // "1001"
```

**规则 6: 类型转换的隐藏规则**

Attribute 总是字符串，但 Property 可能是其他类型：

```javascript
// 数字类型
const input = document.createElement('input');
input.type = 'number';

input.value = 42; // 设置 Property（自动转为字符串）
console.log(typeof input.value);        // "string"
console.log(input.value);               // "42"
console.log(input.valueAsNumber);       // 42（数字类型）

// 布尔类型
const checkbox = document.createElement('input');
checkbox.type = 'checkbox';

checkbox.checked = true;
console.log(typeof checkbox.checked);   // "boolean"
console.log(checkbox.getAttribute('checked')); // ""

// 对象类型
const div = document.createElement('div');

console.log(typeof div.style);          // "object"
console.log(typeof div.classList);      // "object"
console.log(typeof div.dataset);        // "object"
```

---

**记录者注**：

Attribute 和 Property 的同步机制不是简单的"镜像关系"，而是一个精心设计的状态管理系统。

对于不会被用户修改的属性（如 id、className），浏览器维护双向同步，让开发者无需关心用哪种方式访问。对于会被用户修改的属性（如 value、checked），浏览器设计了单向同步 + 脏值标记机制，Attribute 保留初始值用于重置，Property 反映当前状态用于读取。

理解这些同步规则，才能在"读取初始值"、"读取当前值"、"重置表单"等场景中做出正确选择。记住：**当你不确定时，优先使用 Property（更快、更强类型），只有在需要读取 HTML 原始值或处理自定义属性时才用 Attribute。**
