《第 126 次记录：浏览器的既定规则 —— 当我们需要改写世界的默认反应》

## 用户反馈危机

周一上午 9 点 23 分，你收到了一封来自客服部门的紧急邮件。

邮件标题是"用户投诉：表单提交后数据丢失"，附件里有 15 个用户的反馈截图。你点开第一张图片，用户写道："填了 20 分钟的表单，点击提交后页面刷新了，所有数据都没了，太坑了！" 其他用户的反馈也都类似。

你立刻打开测试环境，定位到问题表单——一个包含 30 多个字段的"企业认证申请表"。你填写了几个字段，点击"提交"按钮，页面果然刷新了，控制台里出现了一个 404 错误：`GET /undefined 404`。

"什么情况？" 你打开代码，看到了表单的 HTML 结构：

```html
<form id="certification-form" action="/submit">
  <input type="text" name="company" placeholder="公司名称">
  <input type="email" name="email" placeholder="联系邮箱">
  <!-- 还有 28 个字段... -->
  <button type="submit">提交申请</button>
</form>
```

JavaScript 代码是上周实习生小王写的：

```javascript
const form = document.getElementById('certification-form');
const submitButton = form.querySelector('button[type="submit"]');

submitButton.addEventListener('click', () => {
  const formData = new FormData(form);

  // 发送 AJAX 请求
  fetch('/api/certification', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    alert('提交成功！');
  })
  .catch(error => {
    alert('提交失败：' + error.message);
  });
});
```

"问题找到了，" 你喃喃自语，"小王监听了按钮的点击事件，发送了 AJAX 请求，但没有阻止表单的默认提交行为。所以浏览器既执行了 AJAX，又按照 `<form>` 的 action 属性进行了页面跳转。"

你在监听器里加了一行代码：

```javascript
submitButton.addEventListener('click', (event) => {
  event.preventDefault(); // 阻止默认行为

  const formData = new FormData(form);
  // ... 发送 AJAX
});
```

测试：填写表单，点击提交——这次页面没有刷新，数据通过 AJAX 成功发送，弹出了"提交成功"提示。

"解决了，" 你准备通知客服，但突然想起一个问题：监听器是绑定在按钮上的，而不是表单上。如果用户在输入框里按下回车键呢？

## 表单提交的默认行为

你在表单的输入框里按下回车键——页面又刷新了！

"果然有问题，" 你意识到，"表单提交有两种触发方式：点击提交按钮，或者在输入框里按回车。监听按钮点击事件只覆盖了第一种情况。"

你查阅了 MDN 文档，发现正确的做法是监听表单的 `submit` 事件：

```javascript
const form = document.getElementById('certification-form');

// ❌ 错误做法：监听按钮点击
submitButton.addEventListener('click', (event) => {
  event.preventDefault();
  // ...
});

// ✅ 正确做法：监听表单提交
form.addEventListener('submit', (event) => {
  event.preventDefault(); // 阻止表单默认提交行为

  const formData = new FormData(form);

  fetch('/api/certification', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    alert('提交成功！');
  });
});
```

你测试了两种提交方式：
- 点击提交按钮 → AJAX 提交，页面不刷新 ✅
- 输入框按回车 → AJAX 提交，页面不刷新 ✅

"完美，" 你松了一口气。

前端组的老张路过，看了一眼代码："你知道为什么要用 `preventDefault` 吗？浏览器对很多元素都有默认行为，如果不阻止，就会跟你的自定义逻辑冲突。"

"比如呢？" 你问。

老张打开了一个示例页面：

```html
<!-- 链接的默认行为：跳转 -->
<a href="https://example.com" id="link">跳转</a>

<!-- 复选框的默认行为：切换选中状态 -->
<input type="checkbox" id="checkbox">

<!-- 右键菜单的默认行为：显示上下文菜单 -->
<div id="canvas">右键试试</div>

<!-- 拖拽的默认行为：开始拖拽操作 -->
<div draggable="true" id="draggable">拖动我</div>
```

"每个都有默认行为，" 老张说，"如果你要自定义这些行为，就必须用 `preventDefault()` 阻止浏览器的默认反应。"

## 链接跳转的拦截

老张展示了第一个例子——阻止链接跳转：

```javascript
const link = document.getElementById('link');

link.addEventListener('click', (event) => {
  event.preventDefault(); // 阻止跳转

  console.log('链接被点击，但不会跳转');
  console.log('href:', event.target.href);

  // 可以执行自定义逻辑
  if (confirm('确定要离开本页面吗？')) {
    window.location.href = event.target.href; // 手动跳转
  }
});
```

"这在单页应用（SPA）里很常见，" 老张解释道，"你需要拦截所有链接点击，用前端路由来处理导航，而不是让浏览器刷新页面。"

你尝试了一个更实用的例子——为所有外部链接添加确认提示：

```javascript
document.addEventListener('click', (event) => {
  const link = event.target.closest('a');
  if (!link) return;

  // 判断是否是外部链接
  const currentHost = window.location.hostname;
  const linkHost = new URL(link.href).hostname;

  if (linkHost !== currentHost) {
    event.preventDefault();

    const confirmed = confirm(`即将离开本站，前往 ${linkHost}，确定吗？`);
    if (confirmed) {
      window.open(link.href, link.target || '_blank');
    }
  }
});
```

测试：点击内部链接正常跳转，点击外部链接会弹出确认对话框。"很实用，" 你点头。

## 右键菜单的自定义

老张继续展示第二个例子——自定义右键菜单：

```javascript
const canvas = document.getElementById('canvas');

canvas.addEventListener('contextmenu', (event) => {
  event.preventDefault(); // 阻止默认的右键菜单

  console.log('右键点击位置:', event.clientX, event.clientY);

  // 显示自定义菜单
  showCustomMenu(event.clientX, event.clientY);
});

function showCustomMenu(x, y) {
  const menu = document.createElement('div');
  menu.className = 'custom-menu';
  menu.style.position = 'fixed';
  menu.style.left = x + 'px';
  menu.style.top = y + 'px';
  menu.innerHTML = `
    <div class="menu-item">复制</div>
    <div class="menu-item">粘贴</div>
    <div class="menu-item">删除</div>
  `;

  document.body.appendChild(menu);

  // 点击页面其他地方关闭菜单
  document.addEventListener('click', () => {
    menu.remove();
  }, { once: true });
}
```

"很多在线编辑器、图片编辑器都需要自定义右键菜单，" 老张说，"如果不阻止默认行为，浏览器的右键菜单会和你的自定义菜单同时出现，体验很差。"

你测试了一下，右键点击 canvas 区域，只显示自定义菜单，浏览器的默认菜单被完全禁用了。

## 拖拽行为的控制

老张展示了拖拽的例子：

```javascript
const draggable = document.getElementById('draggable');
const dropZone = document.getElementById('drop-zone');

// 开始拖拽
draggable.addEventListener('dragstart', (event) => {
  event.dataTransfer.setData('text/plain', event.target.id);
  event.target.style.opacity = '0.5';
});

// 拖拽结束
draggable.addEventListener('dragend', (event) => {
  event.target.style.opacity = '1';
});

// 允许放置：必须阻止 dragover 的默认行为
dropZone.addEventListener('dragover', (event) => {
  event.preventDefault(); // 关键！允许放置
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('drag-over');
});

// 放置
dropZone.addEventListener('drop', (event) => {
  event.preventDefault(); // 阻止浏览器打开拖放的文件

  const id = event.dataTransfer.getData('text/plain');
  const draggableElement = document.getElementById(id);

  dropZone.appendChild(draggableElement);
  dropZone.classList.remove('drag-over');
});
```

"注意 `dragover` 事件，" 老张指着代码说，"如果不调用 `preventDefault()`，浏览器会认为这个区域不允许放置，`drop` 事件根本不会触发。"

你测试了一下，确实如此。当你注释掉 `dragover` 里的 `preventDefault()`，拖拽元素到目标区域时，鼠标光标变成了禁止符号，松开鼠标后元素弹回原位。

"这是一个很容易踩的坑，" 老张说，"很多人只在 `drop` 里调用 `preventDefault()`，忘了在 `dragover` 里也要调用。"

## 键盘事件的拦截

老张展示了最后一个例子——拦截快捷键：

```javascript
// 禁用 Ctrl+S（保存页面）
document.addEventListener('keydown', (event) => {
  if (event.ctrlKey && event.key === 's') {
    event.preventDefault(); // 阻止浏览器保存页面

    console.log('自定义保存逻辑');
    saveDocument();
  }
});

// 禁用 F5（刷新页面）
document.addEventListener('keydown', (event) => {
  if (event.key === 'F5') {
    event.preventDefault();
    console.log('刷新被禁用');
  }
});

// 禁用退格键的后退功能
document.addEventListener('keydown', (event) => {
  if (event.key === 'Backspace') {
    const target = event.target;
    // 只在非输入元素上阻止
    if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
      event.preventDefault();
    }
  }
});
```

"这在富文本编辑器里很常见，" 老张说，"你需要自定义各种快捷键的行为，同时阻止浏览器的默认操作。"

你尝试按下 Ctrl+S，浏览器的保存对话框没有弹出，控制台输出了"自定义保存逻辑"。

## 无法阻止的默认行为

老张突然问："你知道有些默认行为是无法阻止的吗？"

你摇头。老张写了一个例子：

```javascript
// 尝试阻止页面关闭
window.addEventListener('beforeunload', (event) => {
  event.preventDefault(); // 无效！
  event.returnValue = ''; // 必须设置这个属性

  return '确定要离开吗？'; // 现代浏览器会忽略这个消息
});

// 尝试阻止滚动（passive 监听器）
document.addEventListener('touchmove', (event) => {
  event.preventDefault(); // ⚠️ 如果监听器是 passive，这行会被忽略
}, { passive: true });

// 正确做法：不设置 passive
document.addEventListener('touchmove', (event) => {
  event.preventDefault(); // 有效
}, { passive: false });
```

"还有一些事件根本不可取消，" 老张补充道，"可以通过 `event.cancelable` 属性检查。"

```javascript
element.addEventListener('click', (event) => {
  console.log('可取消？', event.cancelable); // true

  if (event.cancelable) {
    event.preventDefault(); // 安全地阻止
  } else {
    console.warn('此事件的默认行为无法阻止');
  }
});
```

下午 4 点，你把所有修复提交到 Git，并给客服团队发了一封邮件："表单提交问题已修复，现在所有提交都通过 AJAX 进行，不会导致页面刷新和数据丢失。"

## 默认行为阻止法则

**规则 1: preventDefault 阻止默认行为但不影响事件传播**

`event.preventDefault()` 只阻止浏览器的默认行为（如链接跳转、表单提交、右键菜单），不影响事件的冒泡和捕获。可以与 `stopPropagation()` 组合使用。

```javascript
// 阻止链接跳转
link.addEventListener('click', (event) => {
  event.preventDefault(); // 不跳转
  console.log('链接被点击');
  // 事件继续冒泡到父元素
});

// 阻止表单提交
form.addEventListener('submit', (event) => {
  event.preventDefault(); // 不提交

  // 自定义提交逻辑
  const formData = new FormData(event.target);
  fetch('/api/submit', { method: 'POST', body: formData });
});

// 同时阻止默认行为和事件传播
button.addEventListener('click', (event) => {
  event.preventDefault();      // 阻止默认行为
  event.stopPropagation();     // 阻止冒泡
  // 两者互不影响，可以同时使用
});
```

**规则 2: 表单提交应监听 submit 事件而非按钮点击**

表单可以通过点击提交按钮或在输入框按回车键触发提交。监听表单的 `submit` 事件可以同时覆盖这两种情况，而监听按钮的 `click` 事件只能覆盖第一种。

```javascript
const form = document.querySelector('form');

// ❌ 错误：只能拦截按钮点击，无法拦截回车提交
const submitButton = form.querySelector('button[type="submit"]');
submitButton.addEventListener('click', (event) => {
  event.preventDefault();
  // 用户在输入框按回车时，这里不会执行
});

// ✅ 正确：同时拦截按钮点击和回车提交
form.addEventListener('submit', (event) => {
  event.preventDefault();

  // 验证表单
  if (!validateForm(event.target)) {
    return;
  }

  // 自定义提交逻辑
  const formData = new FormData(event.target);
  fetch('/api/submit', { method: 'POST', body: formData })
    .then(response => response.json())
    .then(data => {
      console.log('提交成功');
    });
});
```

**规则 3: 拖放操作必须在 dragover 中阻止默认行为**

浏览器默认不允许在大多数元素上放置拖拽内容。要允许放置，必须在 `dragover` 事件中调用 `preventDefault()`，否则 `drop` 事件不会触发。

```javascript
const dropZone = document.querySelector('.drop-zone');

// ❌ 错误：只在 drop 中阻止，拖拽仍然不允许
dropZone.addEventListener('drop', (event) => {
  event.preventDefault();
  // 这段代码永远不会执行，因为 dragover 没有阻止默认行为
});

// ✅ 正确：必须在 dragover 中阻止默认行为
dropZone.addEventListener('dragover', (event) => {
  event.preventDefault(); // 允许放置
  // 可以设置视觉反馈
  event.dataTransfer.dropEffect = 'copy';
});

dropZone.addEventListener('drop', (event) => {
  event.preventDefault(); // 阻止浏览器打开拖放的文件

  // 处理放置的数据
  const data = event.dataTransfer.getData('text/plain');
  console.log('放置的数据:', data);
});

// 完整的拖拽示例
const draggable = document.querySelector('.draggable');

draggable.addEventListener('dragstart', (event) => {
  event.dataTransfer.setData('text/plain', 'Hello');
  event.dataTransfer.effectAllowed = 'copy';
});

dropZone.addEventListener('dragover', (event) => {
  event.preventDefault(); // 必须！
});

dropZone.addEventListener('drop', (event) => {
  event.preventDefault(); // 必须！
  const data = event.dataTransfer.getData('text/plain');
  dropZone.textContent = data;
});
```

**规则 4: 使用 cancelable 属性检查事件是否可取消**

并非所有事件都允许阻止默认行为。`event.cancelable` 属性指示事件的默认行为是否可以被 `preventDefault()` 阻止。

```javascript
element.addEventListener('click', (event) => {
  console.log('可取消？', event.cancelable); // true (click 可取消)

  if (event.cancelable) {
    event.preventDefault(); // 安全
  } else {
    console.warn('此事件无法取消');
  }
});

// 不可取消的事件示例
window.addEventListener('scroll', (event) => {
  console.log('可取消？', event.cancelable); // false
  event.preventDefault(); // 无效！scroll 事件不可取消
});

// touchmove 在 passive 模式下不可取消
document.addEventListener('touchmove', (event) => {
  console.log('可取消？', event.cancelable); // false (passive: true)
  event.preventDefault(); // ⚠️ 会在控制台报警告
}, { passive: true });

// 设置 passive: false 使其可取消
document.addEventListener('touchmove', (event) => {
  console.log('可取消？', event.cancelable); // true
  event.preventDefault(); // 有效
}, { passive: false });
```

**规则 5: passive 监听器无法阻止默认行为**

设置了 `passive: true` 的事件监听器，`preventDefault()` 调用会被忽略并在控制台报警告。passive 用于告诉浏览器"我不会阻止默认行为"，从而提升滚动性能。

```javascript
// ❌ 冲突：passive: true + preventDefault()
document.addEventListener('touchstart', (event) => {
  event.preventDefault(); // ⚠️ 被忽略，控制台报警告
  console.log('touch started');
}, { passive: true });

// ✅ 正确：需要阻止默认行为时，不使用 passive
document.addEventListener('touchstart', (event) => {
  event.preventDefault(); // 有效
  console.log('touch started');
}, { passive: false }); // 或省略（默认 false）

// ✅ 正确：只监听不阻止时，使用 passive 提升性能
document.addEventListener('scroll', (event) => {
  console.log('scrolling...');
  // 不调用 preventDefault()
}, { passive: true });

// 注意：Chrome 56+ 对 touchstart/touchmove/wheel 默认 passive: true
// 如果需要阻止默认行为，必须显式设置 passive: false
```

**规则 6: 常见默认行为及其阻止场景**

不同元素和事件有不同的默认行为，阻止它们适用于不同的场景。

```javascript
// 1. 链接跳转 - 单页应用路由
document.addEventListener('click', (event) => {
  const link = event.target.closest('a');
  if (link) {
    event.preventDefault();
    // 使用前端路由导航
    router.push(link.pathname);
  }
});

// 2. 表单提交 - AJAX 提交
form.addEventListener('submit', (event) => {
  event.preventDefault();
  fetch('/api/submit', { method: 'POST', body: new FormData(event.target) });
});

// 3. 右键菜单 - 自定义上下文菜单
canvas.addEventListener('contextmenu', (event) => {
  event.preventDefault();
  showCustomMenu(event.clientX, event.clientY);
});

// 4. 复选框切换 - 自定义切换逻辑
checkbox.addEventListener('click', (event) => {
  event.preventDefault();
  customToggle(checkbox);
});

// 5. 文本选择 - 禁止选择文本
document.addEventListener('selectstart', (event) => {
  event.preventDefault();
});

// 6. 拖拽文件 - 自定义文件上传
document.addEventListener('drop', (event) => {
  event.preventDefault(); // 阻止浏览器打开文件
  const files = event.dataTransfer.files;
  uploadFiles(files);
});

// 7. 快捷键 - 自定义编辑器快捷键
document.addEventListener('keydown', (event) => {
  if (event.ctrlKey && event.key === 's') {
    event.preventDefault(); // 阻止浏览器保存页面
    saveDocument();
  }
});

// 8. 滚动 - 阻止页面滚动（模态框）
modal.addEventListener('wheel', (event) => {
  event.preventDefault();
}, { passive: false });
```

---

**记录者注**:

浏览器为用户交互定义了一套默认行为：点击链接会跳转，提交表单会刷新页面，右键会显示菜单，拖拽文件会打开它。这些默认行为在大多数情况下是合理的，但当我们要构建自定义交互时，就必须用 `preventDefault()` 来改写这些规则。

关键点在于理解哪些行为需要阻止，何时阻止。表单提交监听 `submit` 而非按钮点击，拖放操作在 `dragover` 和 `drop` 都需要阻止，passive 监听器与 preventDefault 互斥。检查 `event.cancelable` 可以避免无效的阻止调用。

记住：**`preventDefault()` 改写浏览器的默认规则，但不影响事件传播。正确使用它，是构建自定义交互体验的基础**。
