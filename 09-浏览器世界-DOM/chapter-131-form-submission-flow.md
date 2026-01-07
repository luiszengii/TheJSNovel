《第 131 次记录：表单的旅程 —— 从提交按钮到服务器的完整链路》

## 重复提交灾难

周一上午 9 点 42 分，你收到了运营部门的紧急电话："用户下单时重复扣款了！"

你立刻打开数据库，查询最近的订单记录。果然，有十几个用户的订单出现了重复：同一时间提交了 2-3 个完全相同的订单。你检查了支付日志，发现这些用户确实被重复扣款了。

"怎么会这样？" 你打开订单提交页面的代码：

```javascript
const form = document.querySelector('.order-form');
const submitButton = form.querySelector('button[type="submit"]');

form.addEventListener('submit', (event) => {
  event.preventDefault();

  const formData = new FormData(form);

  // 发送订单
  fetch('/api/orders', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    alert('订单提交成功！');
    window.location.href = '/orders/' + data.orderId;
  })
  .catch(error => {
    alert('提交失败：' + error.message);
  });
});
```

你在测试环境重现问题：填写订单表单，快速连续点击提交按钮两次 —— 两个请求都发出去了！控制台显示两个 POST 请求，间隔只有 200ms。

"问题找到了，" 你自言自语，"没有防止重复提交。用户点击提交按钮后，如果网络慢或者手快，可能会多次点击，导致重复提交。"

前端负责人老周走过来："这是典型的防重复提交问题。你需要在提交开始时禁用按钮，并添加加载状态。"

## 第一版防重复提交

老周展示了基本的防重复提交方案：

```javascript
const form = document.querySelector('.order-form');
const submitButton = form.querySelector('button[type="submit"]');

let isSubmitting = false; // 提交状态标志

form.addEventListener('submit', (event) => {
  event.preventDefault();

  // 检查是否正在提交
  if (isSubmitting) {
    console.log('正在提交中，忽略重复提交');
    return;
  }

  isSubmitting = true;

  // 禁用提交按钮
  submitButton.disabled = true;
  submitButton.textContent = '提交中...';

  const formData = new FormData(form);

  fetch('/api/orders', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    alert('订单提交成功！');
    window.location.href = '/orders/' + data.orderId;
  })
  .catch(error => {
    alert('提交失败：' + error.message);

    // 恢复按钮状态
    isSubmitting = false;
    submitButton.disabled = false;
    submitButton.textContent = '提交订单';
  });
});
```

你测试了一下：快速点击提交按钮多次，只有第一次点击发送了请求，后续点击被忽略。按钮变成灰色，文字变成"提交中..."。"解决了！" 你准备提交代码。

但老周说："还有几个问题。第一，如果用户在输入框按回车提交呢？第二，如果服务器返回成功但跳转失败呢？第三，如果用户刷新页面重新提交呢？"

## 完善的表单提交流程

老周展示了更完善的方案：

```javascript
class FormSubmitter {
  constructor(form) {
    this.form = form;
    this.submitButton = form.querySelector('button[type="submit"]');
    this.isSubmitting = false;
    this.submissionId = null; // 提交唯一标识
    this.init();
  }

  init() {
    this.form.addEventListener('submit', this.handleSubmit);

    // 监听页面卸载
    window.addEventListener('beforeunload', this.handleBeforeUnload);
  }

  handleSubmit = (event) => {
    event.preventDefault();

    // 防止重复提交
    if (this.isSubmitting) {
      console.log('正在提交中');
      return;
    }

    // 验证表单
    if (!this.validateForm()) {
      return;
    }

    // 生成提交 ID（防止页面刷新重复提交）
    this.submissionId = Date.now() + '-' + Math.random().toString(36).substr(2, 9);

    this.startSubmission();
    this.submit();
  }

  validateForm() {
    // 检查必填字段
    const requiredFields = this.form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
      if (!field.value.trim()) {
        this.showError(field, '此字段为必填项');
        isValid = false;
      }
    });

    return isValid;
  }

  startSubmission() {
    this.isSubmitting = true;

    // 禁用提交按钮
    this.submitButton.disabled = true;
    this.submitButton.setAttribute('aria-busy', 'true');

    // 更新按钮文字和样式
    this.originalButtonText = this.submitButton.textContent;
    this.submitButton.textContent = '提交中...';
    this.submitButton.classList.add('loading');

    // 禁用所有表单控件（可选）
    // this.disableFormControls();
  }

  endSubmission(success = false) {
    if (success) {
      // 成功时不恢复状态，防止重复提交
      return;
    }

    this.isSubmitting = false;

    // 恢复提交按钮
    this.submitButton.disabled = false;
    this.submitButton.removeAttribute('aria-busy');
    this.submitButton.textContent = this.originalButtonText;
    this.submitButton.classList.remove('loading');
  }

  async submit() {
    try {
      const formData = new FormData(this.form);

      // 添加提交 ID 到表单数据
      formData.append('submissionId', this.submissionId);

      const response = await fetch('/api/orders', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // 提交成功
      this.onSuccess(data);
    } catch (error) {
      // 提交失败
      this.onError(error);
    }
  }

  onSuccess(data) {
    console.log('提交成功:', data);

    // 显示成功提示
    this.showSuccessMessage('订单提交成功！');

    // 清除本地草稿
    this.clearDraft();

    // 跳转到订单详情页
    setTimeout(() => {
      window.location.href = '/orders/' + data.orderId;
    }, 1000);
  }

  onError(error) {
    console.error('提交失败:', error);

    // 恢复表单状态
    this.endSubmission(false);

    // 显示错误提示
    this.showErrorMessage('提交失败：' + error.message);
  }

  handleBeforeUnload = (event) => {
    if (this.isSubmitting) {
      // 提交进行中，提示用户
      event.preventDefault();
      event.returnValue = '订单正在提交中，确定要离开吗？';
      return event.returnValue;
    }
  }

  showError(field, message) {
    // 显示字段错误
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    field.parentElement.appendChild(errorElement);

    field.classList.add('error');
    field.focus();
  }

  showSuccessMessage(message) {
    // 显示成功提示
    const toast = document.createElement('div');
    toast.className = 'toast success';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
  }

  showErrorMessage(message) {
    // 显示错误提示
    const toast = document.createElement('div');
    toast.className = 'toast error';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 5000);
  }

  clearDraft() {
    localStorage.removeItem('order-draft');
  }

  destroy() {
    this.form.removeEventListener('submit', this.handleSubmit);
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
  }
}

// 使用表单提交器
const form = document.querySelector('.order-form');
const submitter = new FormSubmitter(form);
```

老周解释道："这个方案处理了几个关键问题：第一，用状态标志防止重复点击；第二，禁用按钮并显示加载状态；第三，添加提交 ID 防止页面刷新重复提交；第四，提交中离开页面时提示用户。"

## 服务端幂等性

老周继续说："前端防重复提交只是一层保护，服务端也必须实现幂等性。你需要把提交 ID 发给后端，后端用它来判断是否是重复请求。"

他展示了服务端的简单实现（伪代码）：

```javascript
// 后端伪代码
const submissionCache = new Map();

app.post('/api/orders', async (req, res) => {
  const { submissionId, ...orderData } = req.body;

  // 检查提交 ID 是否已处理
  if (submissionCache.has(submissionId)) {
    const cachedResult = submissionCache.get(submissionId);
    console.log('重复提交，返回缓存结果');
    return res.json(cachedResult);
  }

  try {
    // 处理订单
    const order = await createOrder(orderData);

    // 缓存结果（设置过期时间）
    submissionCache.set(submissionId, { orderId: order.id });
    setTimeout(() => {
      submissionCache.delete(submissionId);
    }, 5 * 60 * 1000); // 5 分钟后删除

    res.json({ orderId: order.id });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

"前后端配合，" 老周说，"即使前端防护失效，后端也能识别重复请求并返回相同结果，不会真的创建多个订单。"

## 表单数据的多种获取方式

老周展示了获取表单数据的不同方法：

```javascript
const form = document.querySelector('form');

// 方法 1: FormData API（推荐）
form.addEventListener('submit', (event) => {
  event.preventDefault();

  const formData = new FormData(form);

  // 遍历所有字段
  for (const [key, value] of formData.entries()) {
    console.log(key, value);
  }

  // 转换为对象
  const data = Object.fromEntries(formData);
  console.log(data);

  // 发送到服务器
  fetch('/api/submit', {
    method: 'POST',
    body: formData // 直接发送 FormData
  });
});

// 方法 2: 手动收集
form.addEventListener('submit', (event) => {
  event.preventDefault();

  const data = {
    name: form.elements.name.value,
    email: form.elements.email.value,
    message: form.elements.message.value
  };

  console.log(data);

  fetch('/api/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
});

// 方法 3: 使用 name 属性
form.addEventListener('submit', (event) => {
  event.preventDefault();

  const data = {
    name: form.name.value,        // 访问 name="name" 的字段
    email: form.email.value,      // 访问 name="email" 的字段
    message: form.message.value   // 访问 name="message" 的字段
  };

  console.log(data);
});
```

老周特别强调："FormData API 是最推荐的方式，它自动处理文件上传、多选框、单选框等复杂情况。"

## 文件上传处理

老周展示了如何处理文件上传：

```javascript
const form = document.querySelector('.upload-form');
const fileInput = form.querySelector('input[type="file"]');
const progressBar = document.querySelector('.progress-bar');

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData(form);

  // 检查文件大小
  const file = fileInput.files[0];
  if (file && file.size > 10 * 1024 * 1024) {
    alert('文件大小不能超过 10MB');
    return;
  }

  try {
    // 使用 XMLHttpRequest 监听上传进度
    await uploadWithProgress(formData, (percent) => {
      progressBar.style.width = percent + '%';
      progressBar.textContent = percent + '%';
    });

    alert('上传成功！');
  } catch (error) {
    alert('上传失败：' + error.message);
  }
});

function uploadWithProgress(formData, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // 监听上传进度
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    });

    // 监听完成
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`HTTP ${xhr.status}`));
      }
    });

    // 监听错误
    xhr.addEventListener('error', () => {
      reject(new Error('网络错误'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('上传被取消'));
    });

    xhr.open('POST', '/api/upload');
    xhr.send(formData);
  });
}
```

## 表单验证时机

老周展示了不同的表单验证时机：

```javascript
const form = document.querySelector('form');

// 1. 提交时验证（最基本）
form.addEventListener('submit', (event) => {
  if (!validateForm(form)) {
    event.preventDefault();
    alert('请填写所有必填字段');
  }
});

// 2. 失去焦点时验证（实时反馈）
form.addEventListener('focusout', (event) => {
  if (event.target.matches('input, textarea')) {
    validateField(event.target);
  }
});

// 3. 输入时验证（即时反馈，但可能过于频繁）
form.addEventListener('input', (event) => {
  if (event.target.matches('input, textarea')) {
    // 使用防抖避免过于频繁
    debounce(() => {
      validateField(event.target);
    }, 500);
  }
});

// 验证函数
function validateField(field) {
  const value = field.value.trim();
  const type = field.type;
  const name = field.name;

  // 必填验证
  if (field.hasAttribute('required') && !value) {
    showFieldError(field, '此字段为必填项');
    return false;
  }

  // 邮箱验证
  if (type === 'email' && value) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      showFieldError(field, '请输入有效的邮箱地址');
      return false;
    }
  }

  // 手机号验证
  if (name === 'phone' && value) {
    const phoneRegex = /^1[3-9]\d{9}$/;
    if (!phoneRegex.test(value)) {
      showFieldError(field, '请输入有效的手机号');
      return false;
    }
  }

  // 通过验证
  clearFieldError(field);
  return true;
}

function validateForm(form) {
  const fields = form.querySelectorAll('input, textarea, select');
  let isValid = true;

  fields.forEach(field => {
    if (!validateField(field)) {
      isValid = false;
    }
  });

  return isValid;
}

function showFieldError(field, message) {
  clearFieldError(field);

  const errorElement = document.createElement('div');
  errorElement.className = 'field-error';
  errorElement.textContent = message;

  field.classList.add('error');
  field.parentElement.appendChild(errorElement);
}

function clearFieldError(field) {
  field.classList.remove('error');

  const errorElement = field.parentElement.querySelector('.field-error');
  if (errorElement) {
    errorElement.remove();
  }
}
```

下午 4 点，你完成了订单表单的重构。新的提交流程包含了防重复提交、进度提示、完善的错误处理、表单验证等功能。你给运营部门发消息："订单重复提交问题已修复，前后端都增加了防护措施，不会再出现重复扣款了。"

## 表单提交流程法则

**规则 1: 监听 submit 事件而非按钮 click**

表单可以通过点击提交按钮或在输入框按回车键触发提交。监听表单的 `submit` 事件可以同时覆盖这两种情况。

```javascript
const form = document.querySelector('form');
const submitButton = form.querySelector('button[type="submit"]');

// ❌ 错误：只监听按钮点击
submitButton.addEventListener('click', (event) => {
  event.preventDefault();
  handleSubmit();
  // ⚠️ 用户在输入框按回车时不会触发
});

// ✅ 正确：监听表单 submit 事件
form.addEventListener('submit', (event) => {
  event.preventDefault();
  handleSubmit();
  // 点击按钮或按回车都会触发
});

// submit 事件的触发条件：
// 1. 点击 <button type="submit">
// 2. 点击 <input type="submit">
// 3. 在输入框按 Enter 键（单行输入框）
// 4. 调用 form.submit()（不触发 submit 事件）
// 5. 调用 form.requestSubmit()（触发 submit 事件）
```

**规则 2: 实现防重复提交机制**

使用状态标志和禁用按钮防止用户在提交过程中重复点击。提交成功前不恢复按钮状态，提交失败时恢复状态允许重试。

```javascript
class FormSubmitGuard {
  constructor(form) {
    this.form = form;
    this.submitButton = form.querySelector('button[type="submit"]');
    this.isSubmitting = false;
  }

  async handleSubmit(event) {
    event.preventDefault();

    // 防止重复提交
    if (this.isSubmitting) {
      console.log('正在提交中，忽略重复请求');
      return;
    }

    this.startSubmission();

    try {
      const formData = new FormData(this.form);
      const response = await fetch('/api/submit', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      this.onSuccess(data);
      // ✅ 成功时不恢复状态，防止重复提交
    } catch (error) {
      this.endSubmission(); // ✅ 失败时恢复状态，允许重试
      this.onError(error);
    }
  }

  startSubmission() {
    this.isSubmitting = true;
    this.submitButton.disabled = true;
    this.originalText = this.submitButton.textContent;
    this.submitButton.textContent = '提交中...';
    this.submitButton.classList.add('loading');
  }

  endSubmission() {
    this.isSubmitting = false;
    this.submitButton.disabled = false;
    this.submitButton.textContent = this.originalText;
    this.submitButton.classList.remove('loading');
  }

  onSuccess(data) {
    // 提交成功，不恢复状态
    alert('提交成功！');
    window.location.href = '/success';
  }

  onError(error) {
    alert('提交失败：' + error.message);
  }
}
```

**规则 3: 使用提交 ID 实现幂等性**

生成唯一的提交 ID 并发送给服务器，服务器通过提交 ID 判断是否是重复请求。即使前端防护失效，服务器也能识别并忽略重复提交。

```javascript
class IdempotentFormSubmitter {
  constructor(form) {
    this.form = form;
    this.submissionId = null;
  }

  generateSubmissionId() {
    // 生成唯一 ID: 时间戳 + 随机字符串
    return Date.now() + '-' + Math.random().toString(36).substr(2, 9);
  }

  async handleSubmit(event) {
    event.preventDefault();

    // 生成提交 ID
    this.submissionId = this.generateSubmissionId();

    const formData = new FormData(this.form);
    formData.append('submissionId', this.submissionId);

    try {
      const response = await fetch('/api/orders', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      console.log('订单创建成功:', data);
    } catch (error) {
      console.error('提交失败:', error);
    }
  }
}

// 服务端处理（伪代码）
// const submissionCache = new Map();
//
// app.post('/api/orders', async (req, res) => {
//   const { submissionId, ...orderData } = req.body;
//
//   // 检查是否重复提交
//   if (submissionCache.has(submissionId)) {
//     return res.json(submissionCache.get(submissionId));
//   }
//
//   // 创建订单
//   const order = await createOrder(orderData);
//
//   // 缓存结果（5分钟过期）
//   submissionCache.set(submissionId, { orderId: order.id });
//   setTimeout(() => submissionCache.delete(submissionId), 5 * 60 * 1000);
//
//   res.json({ orderId: order.id });
// });
```

**规则 4: 使用 FormData 获取表单数据**

`FormData` API 自动收集表单数据，正确处理文件上传、多选框、单选框等复杂情况。可以直接发送给服务器或转换为对象。

```javascript
const form = document.querySelector('form');

form.addEventListener('submit', (event) => {
  event.preventDefault();

  // ✅ 推荐：使用 FormData
  const formData = new FormData(form);

  // 直接发送（自动设置 Content-Type）
  fetch('/api/submit', {
    method: 'POST',
    body: formData
  });

  // 或转换为对象
  const data = Object.fromEntries(formData);
  console.log(data);

  // 或转换为 JSON
  const jsonData = JSON.stringify(Object.fromEntries(formData));
  fetch('/api/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: jsonData
  });

  // 添加额外字段
  formData.append('timestamp', Date.now());
  formData.append('token', getAuthToken());

  // 处理文件上传
  const fileInput = form.querySelector('input[type="file"]');
  if (fileInput.files.length > 0) {
    formData.append('file', fileInput.files[0]);
  }
});

// ❌ 不推荐：手动收集（容易遗漏字段）
const data = {
  name: form.name.value,
  email: form.email.value,
  // ⚠️ 忘记收集其他字段
};
```

**规则 5: 处理提交中的页面离开**

用户在表单提交过程中可能关闭标签页或刷新页面。使用 `beforeunload` 事件提示用户，避免数据丢失或重复提交。

```javascript
class SafeFormSubmitter {
  constructor(form) {
    this.form = form;
    this.isSubmitting = false;
    this.init();
  }

  init() {
    this.form.addEventListener('submit', this.handleSubmit);
    window.addEventListener('beforeunload', this.handleBeforeUnload);
  }

  handleSubmit = async (event) => {
    event.preventDefault();
    this.isSubmitting = true;

    try {
      await this.submit();
      this.isSubmitting = false;
      // 提交成功，跳转
      window.location.href = '/success';
    } catch (error) {
      this.isSubmitting = false;
      alert('提交失败');
    }
  }

  handleBeforeUnload = (event) => {
    if (this.isSubmitting) {
      // 提交进行中，提示用户
      event.preventDefault();
      event.returnValue = '表单正在提交中，确定要离开吗？';
      return event.returnValue;
    }
  }

  async submit() {
    const formData = new FormData(this.form);
    const response = await fetch('/api/submit', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error('提交失败');
    }

    return response.json();
  }

  destroy() {
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
  }
}
```

**规则 6: 实现多层次的表单验证**

在提交前验证（必须）、失去焦点时验证（推荐）、输入时验证（可选，使用防抖）三个层次进行表单验证，提供良好的用户体验。

```javascript
class FormValidator {
  constructor(form) {
    this.form = form;
    this.init();
  }

  init() {
    // 1. 提交时验证（必须）
    this.form.addEventListener('submit', (event) => {
      if (!this.validateForm()) {
        event.preventDefault();
        alert('请填写所有必填字段');
      }
    });

    // 2. 失去焦点时验证（推荐）
    this.form.addEventListener('focusout', (event) => {
      if (event.target.matches('input, textarea, select')) {
        this.validateField(event.target);
      }
    });

    // 3. 输入时验证（可选，使用防抖）
    let inputTimeout;
    this.form.addEventListener('input', (event) => {
      if (event.target.matches('input, textarea')) {
        clearTimeout(inputTimeout);
        inputTimeout = setTimeout(() => {
          this.validateField(event.target);
        }, 500); // 输入停止 500ms 后验证
      }
    });
  }

  validateForm() {
    const fields = this.form.querySelectorAll('input, textarea, select');
    let isValid = true;

    fields.forEach(field => {
      if (!this.validateField(field)) {
        isValid = false;
      }
    });

    return isValid;
  }

  validateField(field) {
    const value = field.value.trim();

    // 清除旧的错误提示
    this.clearError(field);

    // 必填验证
    if (field.hasAttribute('required') && !value) {
      this.showError(field, '此字段为必填项');
      return false;
    }

    // 类型验证
    if (field.type === 'email' && value) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        this.showError(field, '请输入有效的邮箱地址');
        return false;
      }
    }

    // 自定义验证
    const customValidation = field.dataset.validate;
    if (customValidation && value) {
      const validationFn = this[customValidation];
      if (validationFn && !validationFn.call(this, value)) {
        this.showError(field, field.dataset.errorMessage || '格式不正确');
        return false;
      }
    }

    return true;
  }

  showError(field, message) {
    field.classList.add('error');
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    field.parentElement.appendChild(errorElement);
  }

  clearError(field) {
    field.classList.remove('error');
    const errorElement = field.parentElement.querySelector('.field-error');
    if (errorElement) {
      errorElement.remove();
    }
  }

  // 自定义验证方法
  validatePhone(value) {
    return /^1[3-9]\d{9}$/.test(value);
  }

  validateIdCard(value) {
    return /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/.test(value);
  }
}

// HTML 使用示例
// <input
//   type="text"
//   name="phone"
//   required
//   data-validate="validatePhone"
//   data-error-message="请输入有效的手机号"
// >
```

---

**记录者注**:

表单提交是用户与服务器交互的关键环节，从用户点击提交按钮到数据安全送达服务器，每一步都可能出现问题。重复提交导致重复扣款，网络中断导致数据丢失，验证不足导致脏数据入库。

完善的表单提交流程需要多层防护：前端用状态标志和禁用按钮防止重复点击，提交 ID 配合服务端幂等性防止重复处理，`beforeunload` 事件防止提交中离开页面。`FormData` API 简化数据收集，多层次验证提升用户体验。

记住：**监听 `submit` 而非按钮 `click`，实现防重复提交，使用提交 ID 保证幂等性，用 `FormData` 收集数据，处理 `beforeunload` 事件，多层次验证表单**。完善的提交流程是数据安全和用户体验的保障。
