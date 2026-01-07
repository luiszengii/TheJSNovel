《第 117 次记录：双重身份之谜 —— Attribute 与 Property 的分裂》

## Code Review 时间

周五下午 3 点，会议室里的投影屏幕亮起。

这是团队每周例行的 Code Review 时间，今天轮到技术主管老王审查你的表单验证代码。你分享屏幕，打开你这周完成的用户注册表单：

```javascript
// 表单验证代码
const form = document.querySelector('.signup-form');
const usernameInput = form.querySelector('#username');
const emailInput = form.querySelector('#email');

form.addEventListener('submit', (e) => {
  e.preventDefault();

  // 验证用户名
  if (usernameInput.value.length < 3) {
    usernameInput.className = 'error';
    return;
  }

  // 验证邮箱
  if (!emailInput.value.includes('@')) {
    emailInput.className = 'error';
    return;
  }

  // 通过验证，提交表单
  submitForm(new FormData(form));
});
```

老王看了看代码，指着第 11 行："这里用 `className` 切换样式，为什么不用 `classList`？"

你愣了一下："它们...不是一样的吗？"

"不太一样，" 老王笑着说，"我们来测试一下多个 class 的情况。"

你打开控制台，输入测试代码：

```javascript
const input = document.querySelector('#username');

// 使用 className
input.className = 'form-control';
console.log(input.className); // "form-control"

input.className = 'form-control error';
console.log(input.className); // "form-control error"

// 再添加一个 class？
input.className = input.className + ' warning';
console.log(input.className); // "form-control error warning"

// 移除 error class？
input.className = input.className.replace('error', '').trim();
console.log(input.className); // "form-control  warning" - 有两个空格！
```

"看，" 老王指着屏幕，"`className` 是字符串，操作起来很麻烦。而且容易出错，比如这里留下了两个空格。"

你点了点头。老王继续演示：

```javascript
// 使用 classList
input.classList.add('error');        // 添加
console.log(input.className);        // "form-control warning error"

input.classList.remove('error');     // 移除
console.log(input.className);        // "form-control warning"

input.classList.toggle('active');    // 切换
console.log(input.className);        // "form-control warning active"

input.classList.contains('warning'); // 检查
// true
```

"这样清晰多了，" 你说，"我之前不知道 `classList` 有这么多方法。"

## 深入讨论

Code Review 继续进行。老王又指出了一个问题：

```javascript
// 你的代码
const emailInput = form.querySelector('#email');

// 获取输入框的值
const email = emailInput.getAttribute('value');
console.log(email); // undefined？
```

"为什么 `getAttribute('value')` 返回 undefined？" 老王问。

你试了试：

```javascript
// 直接访问 property
console.log(emailInput.value); // "user@example.com"

// 使用 getAttribute
console.log(emailInput.getAttribute('value')); // null

// 查看 HTML
console.log(emailInput.outerHTML);
// <input type="email" id="email" placeholder="请输入邮箱">
// 注意：HTML 中没有 value 属性！
```

前端组的小陈也加入了讨论："我之前也搞混过这两个。`getAttribute` 读取的是 HTML 标记中的属性，`element.value` 读取的是 DOM 对象的当前值。"

老王点头："没错。我们来系统地测试一下。"

你们开始在控制台做实验：

```javascript
// 实验 1: id 属性
const input = document.querySelector('#username');

console.log(input.id);                   // "username"
console.log(input.getAttribute('id'));   // "username"

input.id = 'user-name';
console.log(input.getAttribute('id'));   // "user-name"
// id 是同步的！

// 实验 2: value 属性
const emailInput = document.querySelector('#email');

// HTML 中设置了初始值
// <input type="email" value="test@example.com">

console.log(emailInput.getAttribute('value'));  // "test@example.com"
console.log(emailInput.value);                  // "test@example.com"

// 用户在输入框中输入新值
emailInput.value = 'user@example.com';

console.log(emailInput.getAttribute('value'));  // "test@example.com" - 没变！
console.log(emailInput.value);                  // "user@example.com" - 变了！
// value 不同步！

// 实验 3: checked 属性
const checkbox = document.querySelector('#agree');

console.log(checkbox.getAttribute('checked'));  // null
console.log(checkbox.checked);                  // false

// 用户勾选复选框
checkbox.checked = true;

console.log(checkbox.getAttribute('checked'));  // null - 仍然是 null！
console.log(checkbox.checked);                  // true
// checked 也不同步！
```

"原来如此，" 你若有所思，"有些属性是同步的（比如 `id`），有些不同步（比如 `value`、`checked`）。"

老王解释："Attribute 是 HTML 的初始值，Property 是 DOM 对象的当前值。对于 `value` 和 `checked` 这种会被用户修改的属性，它们不同步是有道理的 —— HTML 保留初始值，DOM 对象反映当前状态。"

小陈问："那自定义属性呢？比如 `data-*`？"

"好问题，" 老王打开 MDN，"浏览器提供了专门的 `dataset` API。"

你们一起研究：

```html
<div id="user-card"
     data-user-id="1001"
     data-user-role="admin"
     data-is-active="true">
  用户卡片
</div>
```

```javascript
const card = document.querySelector('#user-card');

// 方式 1: getAttribute
console.log(card.getAttribute('data-user-id'));    // "1001"
console.log(card.getAttribute('data-user-role'));  // "admin"

// 方式 2: dataset API（推荐）
console.log(card.dataset.userId);    // "1001" - 注意驼峰命名！
console.log(card.dataset.userRole);  // "admin"
console.log(card.dataset.isActive);  // "true"

// 设置自定义属性
card.dataset.lastLogin = '2024-01-15';
console.log(card.getAttribute('data-last-login'));  // "2024-01-15"

// 删除自定义属性
delete card.dataset.isActive;
console.log(card.hasAttribute('data-is-active'));  // false
```

"dataset 会自动处理命名转换，" 小陈说，"HTML 中的 `data-user-id` 对应 JavaScript 中的 `dataset.userId`。"

气氛轻松，大家都在学习。

## 代码重构

你开始重构表单验证代码，应用刚学到的知识：

```javascript
// 重构后的表单验证代码
class FormValidator {
  constructor(formElement) {
    this.form = formElement;
    this.setupEventListeners();
  }

  setupEventListeners() {
    this.form.addEventListener('submit', (e) => {
      e.preventDefault();

      // 清除之前的错误状态
      this.clearErrors();

      // 验证所有字段
      const isValid = this.validateAll();

      if (isValid) {
        this.submitForm();
      }
    });

    // 实时验证
    this.form.querySelectorAll('input').forEach(input => {
      input.addEventListener('blur', () => {
        this.validateField(input);
      });
    });
  }

  validateField(input) {
    const rules = input.dataset.validate; // 使用 dataset 读取验证规则

    if (!rules) return true;

    // 解析验证规则
    const ruleList = rules.split(',').map(r => r.trim());

    for (const rule of ruleList) {
      if (rule === 'required' && !input.value.trim()) {
        this.showError(input, '此字段必填');
        return false;
      }

      if (rule.startsWith('minlength:')) {
        const minLength = parseInt(rule.split(':')[1]);
        if (input.value.length < minLength) {
          this.showError(input, `至少需要 ${minLength} 个字符`);
          return false;
        }
      }

      if (rule === 'email' && !input.value.includes('@')) {
        this.showError(input, '请输入有效的邮箱地址');
        return false;
      }
    }

    return true;
  }

  showError(input, message) {
    // 使用 classList 添加错误样式
    input.classList.add('error');

    // 显示错误消息
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    input.parentElement.appendChild(errorDiv);
  }

  clearErrors() {
    // 使用 classList 移除错误样式
    this.form.querySelectorAll('.error').forEach(el => {
      el.classList.remove('error');
    });

    // 移除错误消息
    this.form.querySelectorAll('.error-message').forEach(el => {
      el.remove();
    });
  }

  validateAll() {
    const inputs = this.form.querySelectorAll('input[data-validate]');
    return Array.from(inputs).every(input => this.validateField(input));
  }

  submitForm() {
    const formData = new FormData(this.form);
    console.log('提交表单:', Object.fromEntries(formData));
    // 实际提交逻辑...
  }
}

// 使用
const validator = new FormValidator(document.querySelector('.signup-form'));
```

HTML 结构也更新了：

```html
<form class="signup-form">
  <div class="form-group">
    <label for="username">用户名</label>
    <input
      type="text"
      id="username"
      name="username"
      data-validate="required,minlength:3"
      placeholder="至少3个字符">
  </div>

  <div class="form-group">
    <label for="email">邮箱</label>
    <input
      type="email"
      id="email"
      name="email"
      data-validate="required,email"
      placeholder="请输入邮箱">
  </div>

  <div class="form-group">
    <label>
      <input type="checkbox" id="agree" name="agree" data-validate="required">
      我同意用户协议
    </label>
  </div>

  <button type="submit">注册</button>
</form>
```

你演示了重构后的表单，所有功能正常工作。老王点头："这样更清晰了。用 `classList` 操作样式，用 `dataset` 存储自定义数据，代码可读性提高了很多。"

小陈问："那什么时候用 `getAttribute`，什么时候用 property？"

"一般来说，" 老王总结，"优先使用 property（`element.id`、`element.value`），因为它们是强类型的。只有在需要读取 HTML 原始值，或者处理自定义属性时，才用 `getAttribute`。"

"我也学到了 `dataset` API，" 你说，"之前一直用 `getAttribute('data-xxx')`，现在知道有更好的方法了。"

Code Review 在互相学习的氛围中结束。老王说："这次重构很好，通过 Code Review。"

## 属性系统法则

**规则 1: Attribute 是 HTML 标记，Property 是 DOM 对象属性**

Attribute 和 Property 是两个不同的系统：

```javascript
// HTML 标记（Attribute）
<input id="username" value="admin" class="form-control" data-role="admin">

// DOM 对象（Property）
const input = document.querySelector('#username');
input.id           // "username"
input.value        // "admin"
input.className    // "form-control"
input.dataset      // DOMStringMap {role: "admin"}
```

访问方式对比：

| 访问方式 | 类型 | 示例 | 说明 |
|---------|------|------|------|
| **Attribute** | 字符串 | `element.getAttribute('value')` | 读取 HTML 标记 |
| **Property** | 强类型 | `element.value` | 读取 DOM 对象属性 |
| **Dataset** | DOMStringMap | `element.dataset.role` | 访问 data-* 属性 |

Attribute 的特点：

- ✅ 始终是字符串类型
- ✅ 反映 HTML 的初始状态
- ✅ 可以通过 DevTools 看到
- ✅ 可以通过 `getAttribute`/`setAttribute` 访问

Property 的特点：

- ✅ 有强类型（字符串、数字、布尔、对象等）
- ✅ 反映 DOM 对象的当前状态
- ✅ 可以直接通过 `element.property` 访问
- ✅ 性能更好（不需要字符串解析）

**规则 2: 大部分标准属性会同步，但 value/checked 等不同步**

同步的属性：

```javascript
const input = document.querySelector('#username');

// id 属性 - 完全同步
input.id = 'user-name';
console.log(input.getAttribute('id')); // "user-name"

input.setAttribute('id', 'username');
console.log(input.id); // "username"

// class 属性 - 通过 className 同步
input.className = 'form-control error';
console.log(input.getAttribute('class')); // "form-control error"

input.setAttribute('class', 'form-control');
console.log(input.className); // "form-control"

// title 属性 - 完全同步
input.title = '请输入用户名';
console.log(input.getAttribute('title')); // "请输入用户名"
```

不同步的属性：

```javascript
// value 属性 - 不同步（单向同步）
<input type="text" value="初始值">

const input = document.querySelector('input');

// HTML Attribute 保持初始值
console.log(input.getAttribute('value')); // "初始值"

// DOM Property 反映当前值
console.log(input.value); // "初始值"

// 用户修改输入框
input.value = '新值';

// Attribute 不变（保留初始值）
console.log(input.getAttribute('value')); // "初始值"

// Property 变化（反映当前值）
console.log(input.value); // "新值"

// 修改 Attribute 会影响 Property（仅首次）
input.setAttribute('value', '重置值');
console.log(input.value); // "重置值"

// 但之后用户再修改，Attribute 不会更新
input.value = '用户输入';
console.log(input.getAttribute('value')); // "重置值"

// checked 属性 - 同样不同步
const checkbox = document.querySelector('#agree');

// HTML 中的 checked 属性只是初始状态
<input type="checkbox" checked>

console.log(checkbox.hasAttribute('checked')); // true
console.log(checkbox.checked); // true

// 用户取消勾选
checkbox.checked = false;

// Attribute 不变
console.log(checkbox.hasAttribute('checked')); // true

// Property 变化
console.log(checkbox.checked); // false
```

**规则 3: classList 提供比 className 更强大的 API**

`className` 是字符串，操作繁琐：

```javascript
const element = document.querySelector('.box');

// 添加 class
element.className += ' active'; // 注意前面的空格！

// 移除 class
element.className = element.className.replace('active', '').trim();

// 切换 class
if (element.className.includes('active')) {
  element.className = element.className.replace('active', '');
} else {
  element.className += ' active';
}

// 检查是否包含 class
element.className.includes('active');
```

`classList` 提供面向对象的 API：

```javascript
const element = document.querySelector('.box');

// 添加 class
element.classList.add('active');
element.classList.add('fade-in', 'highlight'); // 可以一次添加多个

// 移除 class
element.classList.remove('active');
element.classList.remove('fade-in', 'highlight');

// 切换 class
element.classList.toggle('active'); // 有则删除，无则添加
element.classList.toggle('active', true); // 强制添加
element.classList.toggle('active', false); // 强制删除

// 替换 class
element.classList.replace('old-class', 'new-class');

// 检查是否包含 class
element.classList.contains('active'); // true/false

// 遍历所有 class
element.classList.forEach(className => {
  console.log(className);
});

// 获取数量
console.log(element.classList.length);

// 通过索引访问
console.log(element.classList[0]);
```

**规则 4: 自定义属性使用 data-* 和 dataset API**

HTML5 规定，自定义属性必须以 `data-` 开头：

```html
<!-- ✅ 正确的自定义属性 -->
<div data-user-id="1001" data-role="admin"></div>

<!-- ❌ 非标准的自定义属性（不推荐） -->
<div user-id="1001" role="admin"></div>
```

使用 `dataset` API 访问：

```javascript
const element = document.querySelector('div');

// 读取
console.log(element.dataset.userId);   // "1001"
console.log(element.dataset.role);     // "admin"

// 写入
element.dataset.lastLogin = '2024-01-15';
element.dataset.isActive = 'true';

// 删除
delete element.dataset.role;

// 检查是否存在
console.log('userId' in element.dataset); // true

// 遍历所有 data-* 属性
for (const key in element.dataset) {
  console.log(key, element.dataset[key]);
}
```

命名转换规则：

```html
<!-- HTML 中使用 kebab-case -->
<div
  data-user-id="1001"
  data-last-login-time="2024-01-15"
  data-is-active="true">
</div>
```

```javascript
// JavaScript 中使用 camelCase
element.dataset.userId          // "1001"
element.dataset.lastLoginTime   // "2024-01-15"
element.dataset.isActive        // "true"

// 对应关系：
// data-user-id        → userId
// data-last-login-time → lastLoginTime
// data-is-active      → isActive
```

**规则 5: getAttribute 返回字符串，Property 可能返回其他类型**

类型差异：

```javascript
// 布尔属性
<input type="checkbox" checked>

const checkbox = document.querySelector('input');

console.log(typeof checkbox.getAttribute('checked')); // "string" ("" 或 null)
console.log(typeof checkbox.checked); // "boolean"

// 数字属性
<input type="number" value="42">

const numberInput = document.querySelector('input');

console.log(typeof numberInput.getAttribute('value')); // "string" ("42")
console.log(typeof numberInput.value); // "string" ("42")
console.log(typeof numberInput.valueAsNumber); // "number" (42)

// 对象属性
const element = document.querySelector('.box');

console.log(typeof element.style); // "object" (CSSStyleDeclaration)
console.log(typeof element.classList); // "object" (DOMTokenList)
console.log(typeof element.dataset); // "object" (DOMStringMap)
```

**规则 6: 布尔属性（disabled、checked）的特殊规则**

布尔属性的行为：

```javascript
// HTML 中，布尔属性的存在即表示 true
<input type="checkbox" checked>        // true
<input type="checkbox">                // false
<button disabled>提交</button>         // true
<button>提交</button>                  // false

// JavaScript 中
const checkbox = document.querySelector('#agree');

// Property 是真正的布尔值
checkbox.checked = true;
checkbox.checked = false;

// Attribute 的存在/不存在表示布尔值
checkbox.setAttribute('checked', '');    // true（任何值都是 true）
checkbox.setAttribute('checked', 'false'); // 仍然是 true！
checkbox.removeAttribute('checked');     // false

// 检查布尔属性
console.log(checkbox.hasAttribute('checked')); // true/false
console.log(checkbox.checked); // true/false

// disabled 属性同理
const button = document.querySelector('button');

button.disabled = true;  // 禁用按钮
button.disabled = false; // 启用按钮

// 等价于：
button.setAttribute('disabled', '');  // 禁用
button.removeAttribute('disabled');   // 启用
```

---

**记录者注**：

Attribute 和 Property 是 DOM 世界的双重身份系统。Attribute 是 HTML 标记，是元素的"出生证明"，记录着初始状态；Property 是 DOM 对象的属性，是元素的"当前身份证"，反映着实时状态。

对于 `value` 和 `checked` 这种会被用户修改的属性，它们的双重身份是分离的。HTML 标记保留初始值（方便重置表单），DOM 对象反映当前值（方便读取用户输入）。这不是 bug，而是精心设计的分工。

理解 Attribute 和 Property 的区别，才能在"读取初始值"和"读取当前值"之间做出正确选择。记住：**优先使用 Property（`element.value`），因为它们是强类型的；只有在需要读取 HTML 原始值时，才用 Attribute（`getAttribute`）。**
