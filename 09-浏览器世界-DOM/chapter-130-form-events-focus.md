《第 130 次记录：焦点的流转 —— 表单元素的注意力之争》

## 自动保存失效之谜

周五下午 2 点 35 分，你正在调试一个"智能表单"功能。

产品需求是："用户在表单中填写内容后，失去焦点时自动保存草稿。" 你实现了这个功能，并在测试环境通过了所有测试用例。但上线后，用户反馈："切换到其他标签页时，表单内容没有保存！"

你检查了代码：

```javascript
const form = document.querySelector('.auto-save-form');
const inputs = form.querySelectorAll('input, textarea');

inputs.forEach(input => {
  input.addEventListener('blur', () => {
    console.log('失去焦点，保存草稿');
    saveDraft(form);
  });
});

function saveDraft(form) {
  const formData = new FormData(form);
  const data = Object.fromEntries(formData);

  localStorage.setItem('draft', JSON.stringify(data));
  console.log('草稿已保存:', data);
}
```

你在本地测试：在输入框输入内容，点击页面其他地方，控制台输出"失去焦点，保存草稿"，localStorage 里也有数据。"没问题啊，" 你困惑地想。

你尝试重现用户的操作：在输入框输入内容，然后按 Ctrl+T 打开新标签页。你切换回原标签页，打开 DevTools，检查 localStorage —— 没有数据！"原来如此，" 你恍然大悟，"切换标签页时，`blur` 事件没有触发！"

前端组的小王说："你应该同时监听 `visibilitychange` 事件，当页面被隐藏时也保存草稿。"

## 焦点事件的完整流程

小王展示了焦点事件的完整列表：

```javascript
const input = document.querySelector('input');

// focus: 元素获得焦点（不冒泡）
input.addEventListener('focus', (event) => {
  console.log('获得焦点');
  console.log('目标元素:', event.target);
});

// blur: 元素失去焦点（不冒泡）
input.addEventListener('blur', (event) => {
  console.log('失去焦点');
});

// focusin: 元素获得焦点（冒泡）
input.addEventListener('focusin', (event) => {
  console.log('获得焦点（冒泡）');
  console.log('来自元素:', event.relatedTarget); // 之前有焦点的元素
});

// focusout: 元素失去焦点（冒泡）
input.addEventListener('focusout', (event) => {
  console.log('失去焦点（冒泡）');
  console.log('去往元素:', event.relatedTarget); // 即将获得焦点的元素
});

// change: 值改变且失去焦点
input.addEventListener('change', (event) => {
  console.log('值改变:', event.target.value);
  // 只在值实际改变时触发
  // 必须先改变值，然后失去焦点
});

// input: 值实时改变
input.addEventListener('input', (event) => {
  console.log('输入中:', event.target.value);
  // 每次输入都触发，不需要失去焦点
});
```

小王特别强调了 `focus` vs `focusin` 的区别：

```javascript
const parent = document.querySelector('.parent');
const child = parent.querySelector('input');

// focus / blur: 不冒泡
parent.addEventListener('focus', () => {
  console.log('parent 获得焦点（不会触发）');
  // ❌ 子元素获得焦点时，这里不会触发（因为不冒泡）
});

// focusin / focusout: 冒泡
parent.addEventListener('focusin', (event) => {
  console.log('parent 或子元素获得焦点');
  console.log('实际获得焦点的元素:', event.target);
  // ✅ 子元素获得焦点时，这里会触发（因为冒泡）
});

// 实际应用：表单容器监听焦点变化
const form = document.querySelector('form');

form.addEventListener('focusin', (event) => {
  // 任何表单元素获得焦点时触发
  console.log('表单内元素获得焦点:', event.target.name);
  highlightFormGroup(event.target);
});

form.addEventListener('focusout', (event) => {
  // 任何表单元素失去焦点时触发
  console.log('表单内元素失去焦点:', event.target.name);
  unhighlightFormGroup(event.target);
});
```

"所以用事件委托处理焦点时，" 小王说，"应该用 `focusin` 和 `focusout`，因为它们会冒泡。"

## relatedTarget 的妙用

小王展示了 `relatedTarget` 属性的用途：

```javascript
const input1 = document.querySelector('#input1');
const input2 = document.querySelector('#input2');
const saveButton = document.querySelector('#save');

input1.addEventListener('focusout', (event) => {
  console.log('input1 失去焦点');
  console.log('焦点去往:', event.relatedTarget);

  // 判断焦点是否移动到保存按钮
  if (event.relatedTarget === saveButton) {
    console.log('用户点击了保存按钮，不验证表单');
    return; // 跳过验证
  }

  // 焦点移到其他地方，进行验证
  validateInput(input1);
});

// 实际应用：表单验证逻辑
const form = document.querySelector('form');

form.addEventListener('focusout', (event) => {
  const currentField = event.target;
  const nextField = event.relatedTarget;

  // 如果焦点移到提交按钮，跳过验证
  if (nextField && nextField.type === 'submit') {
    return;
  }

  // 如果焦点移到重置按钮，跳过验证
  if (nextField && nextField.type === 'reset') {
    return;
  }

  // 正常验证
  if (currentField.matches('input, textarea')) {
    validateField(currentField);
  }
});
```

## 程序化焦点控制

小王展示了如何用 JavaScript 控制焦点：

```javascript
const input = document.querySelector('input');

// 让元素获得焦点
input.focus();

// 让元素失去焦点
input.blur();

// 检查元素是否有焦点
console.log('是否有焦点:', input === document.activeElement);

// 检查当前聚焦的元素
console.log('当前聚焦元素:', document.activeElement);

// 实际应用：模态框打开时聚焦第一个输入框
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  modal.style.display = 'block';

  // 聚焦第一个可聚焦元素
  const firstInput = modal.querySelector('input, textarea, button');
  if (firstInput) {
    firstInput.focus();
  }
}

// 实际应用：表单验证失败时聚焦错误字段
function validateForm(form) {
  const errors = [];

  // 验证所有字段
  const inputs = form.querySelectorAll('input[required]');
  inputs.forEach(input => {
    if (!input.value) {
      errors.push({
        field: input,
        message: '此字段为必填项'
      });
    }
  });

  if (errors.length > 0) {
    // 聚焦第一个错误字段
    errors[0].field.focus();

    // 显示错误提示
    showError(errors[0].message);

    return false;
  }

  return true;
}

// 实际应用：搜索框自动聚焦
window.addEventListener('load', () => {
  const searchInput = document.querySelector('.search-input');
  if (searchInput) {
    // 页面加载完成后自动聚焦搜索框
    searchInput.focus();
  }
});
```

## 焦点陷阱（Focus Trap）

小王展示了如何实现"焦点陷阱"，让焦点只在模态框内循环：

```javascript
class Modal {
  constructor(element) {
    this.element = element;
    this.focusableElements = null;
    this.firstFocusable = null;
    this.lastFocusable = null;
  }

  open() {
    this.element.style.display = 'block';

    // 获取所有可聚焦元素
    this.focusableElements = this.element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    this.firstFocusable = this.focusableElements[0];
    this.lastFocusable = this.focusableElements[this.focusableElements.length - 1];

    // 聚焦第一个元素
    this.firstFocusable.focus();

    // 监听键盘事件
    this.element.addEventListener('keydown', this.handleKeydown);
  }

  handleKeydown = (event) => {
    if (event.key !== 'Tab') return;

    // Shift+Tab：反向 Tab
    if (event.shiftKey) {
      if (document.activeElement === this.firstFocusable) {
        event.preventDefault();
        this.lastFocusable.focus(); // 循环到最后一个
      }
    } else {
      // Tab：正向 Tab
      if (document.activeElement === this.lastFocusable) {
        event.preventDefault();
        this.firstFocusable.focus(); // 循环到第一个
      }
    }
  }

  close() {
    this.element.style.display = 'none';
    this.element.removeEventListener('keydown', this.handleKeydown);

    // 恢复之前的焦点
    if (this.previousFocus) {
      this.previousFocus.focus();
    }
  }
}

// 使用焦点陷阱
const modal = new Modal(document.querySelector('.modal'));

document.querySelector('.open-modal').addEventListener('click', () => {
  modal.open();
});

document.querySelector('.close-modal').addEventListener('click', () => {
  modal.close();
});
```

## tabindex 属性

小王解释了 `tabindex` 属性的作用：

```html
<!-- tabindex="0": 可通过 Tab 键聚焦，按照 DOM 顺序 -->
<div tabindex="0">可以获得焦点的 div</div>

<!-- tabindex="-1": 不能通过 Tab 键聚焦，但可以通过 focus() 聚焦 -->
<div tabindex="-1">通过 JS 聚焦的 div</div>

<!-- tabindex="1" 或更大: 可聚焦，且 tabindex 越小越先聚焦 -->
<!-- ❌ 不推荐使用正数 tabindex，会打乱自然 Tab 顺序 -->
<button tabindex="3">第三个</button>
<button tabindex="1">第一个</button>
<button tabindex="2">第二个</button>
```

```javascript
// 实际应用：让不可聚焦元素可聚焦
const div = document.querySelector('.custom-button');
div.setAttribute('tabindex', '0');

// 现在可以聚焦了
div.focus();

div.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    div.click(); // 模拟点击
  }
});

// 实际应用：临时禁用 Tab 聚焦
const button = document.querySelector('button');
button.setAttribute('tabindex', '-1'); // 不能通过 Tab 聚焦

// 稍后恢复
button.setAttribute('tabindex', '0'); // 恢复 Tab 聚焦
```

## change vs input 事件

小王强调了 `change` 和 `input` 的区别：

```javascript
const input = document.querySelector('input');

// input: 实时触发（每次输入）
input.addEventListener('input', (event) => {
  console.log('输入中:', event.target.value);
  // 适用场景：
  // - 实时搜索
  // - 字符计数
  // - 实时验证
});

// change: 值改变且失去焦点时触发
input.addEventListener('change', (event) => {
  console.log('值改变:', event.target.value);
  // 适用场景：
  // - 提交前验证
  // - 保存草稿
  // - 触发计算
});

// 对比测试
// 1. 输入 "hello"
// input 触发 5 次: h, he, hel, hell, hello
// change 不触发

// 2. 点击页面其他地方（失去焦点）
// input 不触发
// change 触发 1 次: hello

// 3. 再次聚焦，删除 "hello"，输入 "hello"（值没变）
// input 触发 10 次（5次删除 + 5次输入）
// 失去焦点后 change 不触发（因为值没有实际改变）
```

```javascript
// 复选框和单选框
const checkbox = document.querySelector('input[type="checkbox"]');

checkbox.addEventListener('change', (event) => {
  console.log('选中状态:', event.target.checked);
  // change 在点击时立即触发，不需要失去焦点
});

// 下拉框
const select = document.querySelector('select');

select.addEventListener('change', (event) => {
  console.log('选中的值:', event.target.value);
  // change 在选择新选项时立即触发
});
```

## 完善的自动保存方案

小王帮你重构了自动保存功能：

```javascript
class AutoSaveForm {
  constructor(form) {
    this.form = form;
    this.saveTimeout = null;
    this.init();
  }

  init() {
    // 监听输入事件（防抖保存）
    this.form.addEventListener('input', () => {
      this.debounceSave();
    });

    // 监听焦点离开事件（立即保存）
    this.form.addEventListener('focusout', (event) => {
      // 检查焦点是否仍在表单内
      if (!this.form.contains(event.relatedTarget)) {
        console.log('焦点离开表单，立即保存');
        this.save();
      }
    });

    // 监听页面可见性变化（切换标签页时保存）
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        console.log('页面被隐藏，立即保存');
        this.save();
      }
    });

    // 监听页面卸载（离开页面时保存）
    window.addEventListener('beforeunload', () => {
      console.log('页面即将卸载，立即保存');
      this.save();
    });

    // 定期保存（每 30 秒）
    setInterval(() => {
      if (this.hasUnsavedChanges()) {
        console.log('定期保存');
        this.save();
      }
    }, 30000);
  }

  debounceSave() {
    clearTimeout(this.saveTimeout);
    this.saveTimeout = setTimeout(() => {
      this.save();
    }, 1000); // 输入停止 1 秒后保存
  }

  save() {
    clearTimeout(this.saveTimeout);

    const formData = new FormData(this.form);
    const data = Object.fromEntries(formData);

    localStorage.setItem('draft', JSON.stringify(data));
    this.showSaveIndicator();

    console.log('草稿已保存:', data);
  }

  hasUnsavedChanges() {
    const currentData = new FormData(this.form);
    const savedData = localStorage.getItem('draft');

    if (!savedData) return true;

    const current = JSON.stringify(Object.fromEntries(currentData));
    return current !== savedData;
  }

  showSaveIndicator() {
    const indicator = document.querySelector('.save-indicator');
    indicator.textContent = '已保存';
    indicator.style.opacity = '1';

    setTimeout(() => {
      indicator.style.opacity = '0';
    }, 2000);
  }
}

// 使用自动保存
const form = document.querySelector('.auto-save-form');
new AutoSaveForm(form);
```

下午 5 点，你部署了新版本的自动保存功能。这次不仅在失去焦点时保存，还在切换标签页、离开页面、定期保存等多个时机保存草稿。你给产品经理发消息："自动保存功能已优化，现在切换标签页、关闭页面都会自动保存，不会丢失数据了。"

## 表单焦点事件法则

**规则 1: focus 和 focusin 的选择**

`focus` 和 `blur` 不冒泡，适合单个元素的焦点处理；`focusin` 和 `focusout` 冒泡，适合事件委托和容器级别的焦点监听。

```javascript
const input = document.querySelector('input');
const form = document.querySelector('form');

// ✅ 单个元素：使用 focus/blur
input.addEventListener('focus', () => {
  console.log('input 获得焦点');
  input.classList.add('focused');
});

input.addEventListener('blur', () => {
  console.log('input 失去焦点');
  input.classList.remove('focused');
});

// ✅ 事件委托：使用 focusin/focusout（冒泡）
form.addEventListener('focusin', (event) => {
  if (event.target.matches('input, textarea')) {
    console.log('表单元素获得焦点:', event.target.name);
    highlightFormGroup(event.target);
  }
});

form.addEventListener('focusout', (event) => {
  if (event.target.matches('input, textarea')) {
    console.log('表单元素失去焦点:', event.target.name);
    validateField(event.target);
  }
});

// ❌ 错误：对父元素使用 focus（不会触发）
form.addEventListener('focus', () => {
  // 子元素获得焦点时不会触发（因为不冒泡）
});
```

**规则 2: 使用 relatedTarget 判断焦点流向**

`focusout` 和 `focusin` 事件的 `relatedTarget` 属性指示焦点的来源或去向，可用于实现条件逻辑（如跳过特定按钮的验证）。

```javascript
const input = document.querySelector('input');
const submitButton = document.querySelector('button[type="submit"]');
const cancelButton = document.querySelector('button[type="button"]');

input.addEventListener('focusout', (event) => {
  console.log('失去焦点，焦点去往:', event.relatedTarget);

  // 判断焦点是否移到提交或取消按钮
  if (event.relatedTarget === submitButton || event.relatedTarget === cancelButton) {
    console.log('用户点击按钮，跳过验证');
    return;
  }

  // 焦点移到其他输入框或空白处，进行验证
  validateInput(input);
});

// 实际应用：表单焦点流转跟踪
const form = document.querySelector('form');

form.addEventListener('focusin', (event) => {
  console.log('从', event.relatedTarget, '移动到', event.target);

  // 记录焦点流转路径
  trackFocusPath(event.relatedTarget, event.target);
});
```

**规则 3: 实现焦点陷阱确保可访问性**

模态框、对话框等覆盖层打开时，应实现焦点陷阱（focus trap），让 Tab 键焦点只在覆盖层内循环，按 Escape 关闭时恢复原焦点。

```javascript
class FocusTrap {
  constructor(element) {
    this.element = element;
    this.previousFocus = null;
    this.focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  }

  activate() {
    // 保存当前焦点
    this.previousFocus = document.activeElement;

    // 获取可聚焦元素
    this.updateFocusableElements();

    // 聚焦第一个元素
    if (this.firstFocusable) {
      this.firstFocusable.focus();
    }

    // 监听键盘事件
    this.element.addEventListener('keydown', this.handleKeydown);
  }

  updateFocusableElements() {
    const elements = Array.from(this.element.querySelectorAll(this.focusableSelectors));
    this.focusableElements = elements.filter(el => !el.hasAttribute('disabled'));
    this.firstFocusable = this.focusableElements[0];
    this.lastFocusable = this.focusableElements[this.focusableElements.length - 1];
  }

  handleKeydown = (event) => {
    if (event.key === 'Tab') {
      if (event.shiftKey) {
        // Shift+Tab: 反向
        if (document.activeElement === this.firstFocusable) {
          event.preventDefault();
          this.lastFocusable.focus();
        }
      } else {
        // Tab: 正向
        if (document.activeElement === this.lastFocusable) {
          event.preventDefault();
          this.firstFocusable.focus();
        }
      }
    } else if (event.key === 'Escape') {
      // Escape: 关闭
      this.deactivate();
    }
  }

  deactivate() {
    this.element.removeEventListener('keydown', this.handleKeydown);

    // 恢复之前的焦点
    if (this.previousFocus && this.previousFocus.focus) {
      this.previousFocus.focus();
    }
  }
}

// 使用焦点陷阱
const modal = document.querySelector('.modal');
const focusTrap = new FocusTrap(modal);

document.querySelector('.open-modal').addEventListener('click', () => {
  modal.style.display = 'block';
  focusTrap.activate();
});

document.querySelector('.close-modal').addEventListener('click', () => {
  modal.style.display = 'none';
  focusTrap.deactivate();
});
```

**规则 4: 合理使用 tabindex 属性**

使用 `tabindex="0"` 让元素可聚焦，`tabindex="-1"` 让元素通过 JS 聚焦但不可 Tab 聚焦。避免使用正数 `tabindex`，它会打乱自然 Tab 顺序。

```javascript
// ✅ 让 div 可以获得焦点
const customButton = document.querySelector('.custom-button');
customButton.setAttribute('tabindex', '0');

customButton.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    customButton.click();
  }
});

// ✅ 隐藏元素时禁用 Tab 聚焦
const hiddenSection = document.querySelector('.hidden-section');
hiddenSection.querySelectorAll('button, a, input').forEach(el => {
  el.setAttribute('tabindex', '-1');
});

// 显示时恢复
hiddenSection.querySelectorAll('[tabindex="-1"]').forEach(el => {
  el.setAttribute('tabindex', '0');
});

// ❌ 避免使用正数 tabindex
// <button tabindex="1">第一个</button>  <!-- 不推荐 -->
// <button tabindex="2">第二个</button>  <!-- 不推荐 -->
// 会打乱自然的 DOM 顺序，造成混乱

// ✅ 正确做法：调整 DOM 顺序
// <button>第一个</button>
// <button>第二个</button>
```

**规则 5: change 用于最终值，input 用于实时值**

`input` 事件在每次输入时触发，适合实时搜索、字符计数；`change` 事件在值改变且失去焦点时触发（复选框/单选框/下拉框立即触发），适合表单验证、保存草稿。

```javascript
const input = document.querySelector('input');

// ✅ 实时搜索：使用 input
input.addEventListener('input', (event) => {
  const query = event.target.value;
  searchSuggestions(query); // 每次输入都搜索
});

// ✅ 字符计数：使用 input
input.addEventListener('input', (event) => {
  const length = event.target.value.length;
  updateCharCount(length); // 实时更新
});

// ✅ 表单验证：使用 change
input.addEventListener('change', (event) => {
  const value = event.target.value;
  validateField(value); // 输入完成后验证
});

// ✅ 保存草稿：使用 change
input.addEventListener('change', () => {
  saveDraft(); // 失去焦点时保存
});

// 复选框/单选框：change 立即触发
const checkbox = document.querySelector('input[type="checkbox"]');
checkbox.addEventListener('change', (event) => {
  console.log('选中状态:', event.target.checked);
  // 点击时立即触发，无需失去焦点
});

// 下拉框：change 立即触发
const select = document.querySelector('select');
select.addEventListener('change', (event) => {
  console.log('选中的值:', event.target.value);
  // 选择选项时立即触发
});
```

**规则 6: 综合考虑多种保存时机**

自动保存不应只依赖 `blur` 事件，还需处理页面隐藏（`visibilitychange`）、页面卸载（`beforeunload`）、定期保存（`setInterval`）等场景。

```javascript
class AutoSave {
  constructor(form, options = {}) {
    this.form = form;
    this.interval = options.interval || 30000; // 30 秒
    this.debounceDelay = options.debounceDelay || 1000; // 1 秒
    this.saveTimeout = null;
    this.intervalId = null;
    this.init();
  }

  init() {
    // 1. 输入时防抖保存
    this.form.addEventListener('input', () => {
      this.debounceSave();
    });

    // 2. 失去焦点时保存
    this.form.addEventListener('focusout', (event) => {
      if (!this.form.contains(event.relatedTarget)) {
        this.save();
      }
    });

    // 3. 页面隐藏时保存（切换标签页）
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.save();
      }
    });

    // 4. 页面卸载前保存
    window.addEventListener('beforeunload', () => {
      this.save();
    });

    // 5. 定期保存
    this.intervalId = setInterval(() => {
      if (this.hasChanges()) {
        this.save();
      }
    }, this.interval);
  }

  debounceSave() {
    clearTimeout(this.saveTimeout);
    this.saveTimeout = setTimeout(() => this.save(), this.debounceDelay);
  }

  save() {
    clearTimeout(this.saveTimeout);
    const data = new FormData(this.form);
    localStorage.setItem('draft', JSON.stringify(Object.fromEntries(data)));
    this.showIndicator();
  }

  hasChanges() {
    // 检查是否有未保存的更改
    const current = new FormData(this.form);
    const saved = localStorage.getItem('draft');
    return JSON.stringify(Object.fromEntries(current)) !== saved;
  }

  showIndicator() {
    // 显示保存指示器
  }

  destroy() {
    clearInterval(this.intervalId);
    clearTimeout(this.saveTimeout);
  }
}

// 使用自动保存
const autoSave = new AutoSave(document.querySelector('form'), {
  interval: 30000,      // 30 秒定期保存
  debounceDelay: 1000   // 输入停止 1 秒后保存
});
```

---

**记录者注**:

焦点是用户注意力的代理，表单元素通过焦点事件与用户进行交互。`focus` 和 `blur` 不冒泡，适合单个元素；`focusin` 和 `focusout` 冒泡，适合事件委托。`relatedTarget` 揭示焦点的来源和去向，让我们能实现条件逻辑。

焦点陷阱确保模态框的可访问性，`tabindex` 控制 Tab 顺序，`change` 和 `input` 分别处理最终值和实时值。自动保存需要综合考虑失去焦点、页面隐藏、页面卸载、定期保存等多种时机，才能真正不丢失数据。

记住：**`focusin`/`focusout` 用于事件委托，`relatedTarget` 判断焦点流向，实现焦点陷阱确保可访问性，`change` 用于最终值，`input` 用于实时值，多时机保存避免数据丢失**。焦点事件是表单交互的核心。
