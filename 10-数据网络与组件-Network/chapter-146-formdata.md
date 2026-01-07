《第 146 次记录: 客户演示的惊魂 15 分钟 —— FormData 的表单真相》

---

## 演示前的信心

客户演示前 15 分钟, 你坐在会议室的电脑前, 做最后的功能检查。

这是一个重要的演示。客户的 CTO 和技术团队会在 15 分钟后到达, 你要展示公司新开发的智能表单系统——支持文件上传、实时验证、多步骤提交。前端团队花了两个月打磨这个功能, 上周的内部测试非常顺利。

"应该没问题," 你想, 手指在键盘上轻快地敲击着, 准备演示数据。

你打开系统, 测试了一遍核心流程：填写用户信息 → 上传身份证照片 → 选择服务类型 → 提交表单。每一步都流畅无比, 数据提交成功, 后端返回确认信息。

"完美," 你满意地点头, 看了一眼时间——还有 12 分钟。

你决定再测试一个边界情况：同时上传多个文件。你选择了 3 张图片和 1 个 PDF 文件, 点击 "提交"。

然后, 世界静止了 3 秒。

浏览器控制台突然爆出红色错误：

```
POST /api/submit 400 Bad Request
{
  "error": "Invalid form data: expected multipart/form-data"
}
```

"什么?!" 你的心跳突然加速。你刚才明明测试过文件上传, 为什么现在失败了?

你快速检查代码——提交逻辑是前端小陈上周写的：

```javascript
async function submitForm() {
    const formData = {
        name: document.querySelector('#name').value,
        email: document.querySelector('#email').value,
        files: document.querySelector('#files').files
    };

    const response = await fetch('/api/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    });

    return response.json();
}
```

"看起来没问题啊..." 你喃喃自语。但错误提示很明确：服务器期待 `multipart/form-data`, 而不是 JSON。

你看了一眼时间——还有 9 分钟。

---

## 现场翻车

8 分钟后, 客户的 CTO 和 3 位技术负责人走进会议室。

你强作镇定, 打开演示系统："各位好, 今天我们展示的是智能表单系统。首先演示基础功能..."

前面两个功能演示得很顺利——纯文本表单提交、单文件上传都没问题。客户的技术负责人频频点头。

"现在展示批量文件上传," 你说, 手心已经开始冒汗。你选择了 3 个文件, 点击提交...

```
400 Bad Request
```

会议室陷入了短暂的沉默。

客户的 CTO 皱起眉头："是网络问题吗?"

"稍等, 我检查一下," 你强装平静, 但内心已经慌了——你刚才没能修复这个 bug, 现在它在客户面前爆发了。

你打开浏览器控制台, 假装在 "排查网络问题", 实际上你的大脑在飞速运转：

**问题 1**: 为什么单文件上传成功, 但多文件失败?
**线索 1**: 服务器要求 `multipart/form-data`
**线索 2**: 当前代码用的是 `application/json`
**关键**: 文件对象无法被 JSON.stringify 序列化!

"找到了," 你突然说, "是表单编码格式的问题, 需要调整一下。"

你快速修改代码, 手指在键盘上飞舞：

```javascript
async function submitFormFixed() {
    // ✅ 使用 FormData 替代 JSON
    const formData = new FormData();

    formData.append('name', document.querySelector('#name').value);
    formData.append('email', document.querySelector('#email').value);

    // 添加所有选中的文件
    const files = document.querySelector('#files').files;
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    const response = await fetch('/api/submit', {
        method: 'POST',
        // ❌ 不要设置 Content-Type!浏览器会自动设置 multipart/form-data
        body: formData
    });

    return response.json();
}
```

"请稍等 30 秒," 你对客户说, 然后快速部署修复代码。

30 秒后, 你深吸一口气, 重新选择了 3 个文件, 点击提交——

成功了! 后端返回确认信息, 文件全部上传完成。

客户的 CTO 说："不错, 修复得很快。但我有个问题——为什么之前的单文件上传能成功?"

你愣住了。对啊, 为什么?

---

## 危机化解

演示结束后, 你回到工位, 开始深入调查这个诡异的现象。

你重新测试了原始代码：

```javascript
// 测试 1: 单文件上传
const formData = {
    files: document.querySelector('#files').files  // FileList 对象
};

console.log(JSON.stringify(formData));
// {"files":{}}  ❌ FileList 被序列化成空对象!

// 测试 2: 提取单个文件
const formData = {
    files: document.querySelector('#files').files[0]  // File 对象
};

console.log(JSON.stringify(formData));
// {"files":{}}  ❌ File 对象也被序列化成空对象!
```

"所以 JSON 根本无法处理文件对象," 你恍然大悟, "那为什么单文件上传之前能成功?"

你查看了后端代码, 发现了关键线索：

```python
# 后端代码
@app.route('/api/submit', methods=['POST'])
def submit():
    content_type = request.headers.get('Content-Type')

    if content_type == 'application/json':
        # JSON 模式：处理纯文本数据
        data = request.json
        # 如果没有 files 字段，使用默认值
        files = data.get('files', [])

    elif 'multipart/form-data' in content_type:
        # multipart 模式：处理文件数据
        files = request.files.getlist('files')

    # ...
```

"原来如此!" 你终于明白了：

**单文件上传成功的原因**：
- 前端发送 JSON 时, `files` 字段被序列化成空对象 `{}`
- 后端检测到 `application/json`, 进入 JSON 处理逻辑
- `data.get('files', [])` 返回空数组
- 后端把表单当作 "无文件附件" 处理, 所以 "成功" 了
- 但实际上文件根本没有上传! 只是没报错而已

**多文件上传失败的真相**：
- 用户选择多个文件后, 你在演示环境切换了测试账号
- 切换账号后触发了后端的权限检查
- 权限检查发现 "无文件" 的表单不符合业务规则
- 返回 400 错误："必须上传至少 1 个文件"

你倒吸一口凉气——之前的"成功"只是假象, 文件从来没有真正上传过!

---

## 深度理解

你打开一个新的测试文件, 系统地验证 FormData 的特性：

```javascript
// 实验 1: FormData 的本质
const formData = new FormData();

formData.append('name', '张三');
formData.append('age', 25);
formData.append('tags', 'frontend');
formData.append('tags', 'javascript');  // 同名字段可以多次添加

// FormData 不能直接打印
console.log(formData);  // FormData {}

// 必须遍历才能查看内容
for (let [key, value] of formData.entries()) {
    console.log(key, value);
}
// name 张三
// age 25
// tags frontend
// tags javascript
```

"FormData 是一种特殊的对象," 你总结, "它不是普通的 JavaScript 对象, 而是专门用于表单数据传输的容器。"

你继续实验文件上传：

```javascript
// 实验 2: 文件上传的正确姿势
const formData = new FormData();

// 方式 1: 直接从 input 添加文件
const fileInput = document.querySelector('#files');
formData.append('avatar', fileInput.files[0]);  // 单文件

// 方式 2: 批量添加多个文件
const files = document.querySelector('#files').files;
for (let i = 0; i < files.length; i++) {
    formData.append('photos', files[i]);
}

// 方式 3: 使用相同字段名添加多个文件
Array.from(files).forEach(file => {
    formData.append('attachments', file);
});

// 检查文件是否添加成功
for (let [key, value] of formData.entries()) {
    if (value instanceof File) {
        console.log(`${key}: ${value.name} (${value.size} bytes)`);
    }
}
```

你又测试了一个关键问题——Content-Type 的设置：

```javascript
// ❌ 错误 1: 手动设置 Content-Type 为 multipart/form-data
const formData = new FormData();
formData.append('file', file);

fetch('/api/upload', {
    method: 'POST',
    headers: {
        'Content-Type': 'multipart/form-data'  // ❌ 错误!
    },
    body: formData
});
// 问题: 缺少 boundary 参数, 后端无法解析

// ✅ 正确: 完全不设置 Content-Type
fetch('/api/upload', {
    method: 'POST',
    body: formData  // 浏览器自动添加正确的 Content-Type
});
// 浏览器会自动设置:
// Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
```

"boundary!" 你惊呼, "这就是为什么不能手动设置 Content-Type——浏览器需要生成随机的 boundary 标识符来分隔各个字段!"

---

## 表单传输的真相

你创建了一个完整的示例, 展示 FormData 的各种用法：

```javascript
// 场景 1: 纯文本表单
function submitTextForm() {
    const formData = new FormData();

    formData.append('username', 'alice');
    formData.append('email', 'alice@example.com');
    formData.append('role', 'admin');

    return fetch('/api/users', {
        method: 'POST',
        body: formData
    });
}

// 场景 2: 文件上传表单
function submitFileForm() {
    const formData = new FormData();

    // 文本字段
    formData.append('title', '项目报告');
    formData.append('description', '第三季度总结');

    // 单个文件
    const file = document.querySelector('#file').files[0];
    formData.append('document', file);

    return fetch('/api/documents', {
        method: 'POST',
        body: formData
    });
}

// 场景 3: 多文件上传
function submitMultipleFiles() {
    const formData = new FormData();

    formData.append('albumName', '旅行照片');

    // 批量添加文件
    const files = document.querySelector('#photos').files;
    Array.from(files).forEach(file => {
        formData.append('photos', file);  // 使用相同的字段名
    });

    return fetch('/api/albums', {
        method: 'POST',
        body: formData
    });
}

// 场景 4: 混合数据（文本 + 文件 + Blob）
function submitMixedForm() {
    const formData = new FormData();

    // 文本数据
    formData.append('name', '用户头像');

    // 文件数据
    const file = document.querySelector('#avatar').files[0];
    formData.append('avatar', file);

    // Blob 数据（如 Canvas 生成的图片）
    const canvas = document.querySelector('#canvas');
    canvas.toBlob(blob => {
        formData.append('thumbnail', blob, 'thumbnail.png');

        return fetch('/api/profile', {
            method: 'POST',
            body: formData
        });
    });
}

// 场景 5: 从现有表单创建 FormData
function submitExistingForm() {
    const form = document.querySelector('#myForm');
    const formData = new FormData(form);  // 自动提取表单所有字段

    // 可以继续添加额外字段
    formData.append('timestamp', Date.now());
    formData.append('source', 'web');

    return fetch('/api/submit', {
        method: 'POST',
        body: formData
    });
}
```

你又研究了 FormData 的操作方法：

```javascript
const formData = new FormData();

// 1. append(): 添加字段（允许同名字段）
formData.append('tag', 'javascript');
formData.append('tag', 'frontend');  // 同名字段，两个都保留

// 2. set(): 设置字段（覆盖同名字段）
formData.set('tag', 'backend');  // 覆盖之前的所有 tag 字段

// 3. get(): 获取单个值
console.log(formData.get('tag'));  // 'backend'

// 4. getAll(): 获取所有同名字段的值
formData.append('tag', 'database');
console.log(formData.getAll('tag'));  // ['backend', 'database']

// 5. has(): 检查字段是否存在
console.log(formData.has('tag'));  // true
console.log(formData.has('unknown'));  // false

// 6. delete(): 删除字段
formData.delete('tag');
console.log(formData.has('tag'));  // false

// 7. entries(): 遍历所有字段
for (let [key, value] of formData.entries()) {
    console.log(key, value);
}

// 8. keys(): 遍历所有键
for (let key of formData.keys()) {
    console.log(key);
}

// 9. values(): 遍历所有值
for (let value of formData.values()) {
    console.log(value);
}
```

---

## 最佳实践总结

你整理了一份 FormData 使用指南, 准备分享给团队：

```javascript
// ✅ 最佳实践 1: 文件上传必须用 FormData
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData  // ✅ 不设置 Content-Type
    });

    return response.json();
}

// ✅ 最佳实践 2: 带进度监听的上传
function uploadWithProgress(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // 上传进度
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                onProgress(percent);
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(new Error(`Upload failed: ${xhr.status}`));
            }
        };

        xhr.onerror = () => reject(new Error('Network error'));

        xhr.open('POST', '/api/upload');
        xhr.send(formData);
    });
}

// ✅ 最佳实践 3: 表单验证后提交
async function submitValidatedForm(form) {
    // 表单验证
    if (!form.checkValidity()) {
        form.reportValidity();  // 显示验证错误
        return;
    }

    // 创建 FormData
    const formData = new FormData(form);

    // 添加额外字段
    formData.append('timestamp', new Date().toISOString());
    formData.append('userAgent', navigator.userAgent);

    // 提交
    const response = await fetch('/api/submit', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        throw new Error(`Submit failed: ${response.status}`);
    }

    return response.json();
}

// ✅ 最佳实践 4: 处理嵌套对象
async function submitNestedData(data) {
    const formData = new FormData();

    // 简单字段
    formData.append('name', data.name);

    // 嵌套对象需要序列化
    formData.append('profile', JSON.stringify(data.profile));

    // 数组需要逐个添加
    data.tags.forEach(tag => {
        formData.append('tags', tag);
    });

    // 文件
    if (data.avatar) {
        formData.append('avatar', data.avatar);
    }

    return fetch('/api/profile', {
        method: 'POST',
        body: formData
    });
}

// ✅ 最佳实践 5: 动态表单构建
class FormBuilder {
    constructor() {
        this.formData = new FormData();
    }

    addField(name, value) {
        if (value instanceof File || value instanceof Blob) {
            this.formData.append(name, value);
        } else if (Array.isArray(value)) {
            value.forEach(item => {
                this.formData.append(name, item);
            });
        } else if (typeof value === 'object') {
            this.formData.append(name, JSON.stringify(value));
        } else {
            this.formData.append(name, String(value));
        }
        return this;
    }

    addFile(name, file, filename) {
        this.formData.append(name, file, filename);
        return this;
    }

    build() {
        return this.formData;
    }
}

// 使用示例
const builder = new FormBuilder();
const formData = builder
    .addField('name', 'Alice')
    .addField('tags', ['frontend', 'javascript'])
    .addField('profile', { age: 25, city: 'Beijing' })
    .addFile('avatar', file, 'avatar.png')
    .build();
```

你创建了一个常见错误对比表：

```javascript
// ❌ 错误 1: 试图 JSON.stringify FormData
const formData = new FormData();
formData.append('name', 'Alice');
console.log(JSON.stringify(formData));  // ❌ {}

// ✅ 正确: 遍历或直接发送
for (let [key, value] of formData.entries()) {
    console.log(key, value);
}

// ❌ 错误 2: 手动设置 Content-Type
fetch('/api/upload', {
    headers: {
        'Content-Type': 'multipart/form-data'  // ❌ 缺少 boundary
    },
    body: formData
});

// ✅ 正确: 不设置, 让浏览器自动添加
fetch('/api/upload', {
    body: formData  // ✅ 浏览器自动设置正确的 Content-Type
});

// ❌ 错误 3: 假设 FormData 可以像对象一样访问
const formData = new FormData();
formData.append('name', 'Alice');
console.log(formData.name);  // ❌ undefined

// ✅ 正确: 使用 get() 方法
console.log(formData.get('name'));  // ✅ 'Alice'

// ❌ 错误 4: 文件对象 JSON 序列化
const data = {
    name: 'Alice',
    avatar: document.querySelector('#avatar').files[0]
};
fetch('/api/profile', {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)  // ❌ File 对象丢失
});

// ✅ 正确: 使用 FormData
const formData = new FormData();
formData.append('name', 'Alice');
formData.append('avatar', document.querySelector('#avatar').files[0]);
fetch('/api/profile', {
    body: formData  // ✅ 文件正确传输
});

// ❌ 错误 5: 在 Blob 回调外发送请求
const canvas = document.querySelector('#canvas');
const formData = new FormData();

canvas.toBlob(blob => {
    formData.append('image', blob);
});

fetch('/api/image', { body: formData });  // ❌ blob 还没添加完成

// ✅ 正确: 在回调内发送
canvas.toBlob(blob => {
    formData.append('image', blob);
    fetch('/api/image', { body: formData });  // ✅ 确保 blob 已添加
});
```

---

## 知识总结: FormData 的核心原理

**规则 1: FormData 是专门的表单数据容器**

FormData 不是普通的 JavaScript 对象, 而是浏览器提供的专用 API, 用于构建符合 `multipart/form-data` 格式的 HTTP 请求体。

```javascript
const formData = new FormData();

// FormData 的本质
console.log(typeof formData);  // 'object'
console.log(formData instanceof FormData);  // true
console.log(formData instanceof Object);  // true

// 但它不能像对象一样访问
formData.name = 'Alice';  // 无效
console.log(formData.name);  // undefined

// 必须使用专用方法
formData.append('name', 'Alice');
console.log(formData.get('name'));  // 'Alice'
```

核心特性:
- 不可 JSON 序列化: `JSON.stringify(formData)` 返回 `{}`
- 不可直接访问: 无法用 `formData.key` 语法
- 必须遍历查看: 使用 `entries()`, `keys()`, `values()`
- 支持同名字段: `append()` 允许多个同名字段共存

---

**规则 2: Content-Type 必须由浏览器自动设置**

FormData 提交时, 绝对不能手动设置 `Content-Type` 头, 必须让浏览器自动添加。

```javascript
const formData = new FormData();
formData.append('file', file);

// ❌ 错误: 手动设置 Content-Type
fetch('/api/upload', {
    headers: {
        'Content-Type': 'multipart/form-data'  // ❌ 缺少 boundary
    },
    body: formData
});
// 服务器会报错: "Missing boundary parameter"

// ✅ 正确: 完全不设置 Content-Type
fetch('/api/upload', {
    method: 'POST',
    body: formData  // 浏览器自动添加完整的 Content-Type
});
// 浏览器设置的完整头部:
// Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
```

为什么必须自动设置:
- `boundary` 参数: 浏览器生成随机字符串, 用于分隔各个字段
- 格式要求: 手动设置通常会遗漏 `boundary` 参数
- 安全考虑: `boundary` 必须足够随机, 避免与数据内容冲突

---

**规则 3: 文件上传只能用 FormData, 不能用 JSON**

File 对象和 Blob 对象无法被 `JSON.stringify()` 序列化, 必须使用 FormData 传输。

```javascript
const file = document.querySelector('#file').files[0];

// ❌ 错误: JSON 序列化 File 对象
const data = { file: file };
console.log(JSON.stringify(data));  // {"file":{}}  ❌ File 对象丢失

fetch('/api/upload', {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)  // ❌ 文件数据完全丢失
});

// ✅ 正确: 使用 FormData
const formData = new FormData();
formData.append('file', file);

fetch('/api/upload', {
    method: 'POST',
    body: formData  // ✅ 文件正确编码和传输
});
```

为什么 JSON 不行:
- File 对象不可序列化: `JSON.stringify(file)` 返回 `{}`
- Blob 对象同样不行: `JSON.stringify(blob)` 也返回 `{}`
- FileList 也不行: `JSON.stringify(fileList)` 返回 `{}`
- 二进制数据需要特殊编码: `multipart/form-data` 可以正确处理二进制

---

**规则 4: append() 与 set() 的关键区别**

`append()` 允许同名字段多次添加, `set()` 会覆盖同名字段。

```javascript
const formData = new FormData();

// append(): 允许同名字段
formData.append('tag', 'javascript');
formData.append('tag', 'frontend');
formData.append('tag', 'react');

console.log(formData.getAll('tag'));
// ['javascript', 'frontend', 'react']  ✅ 三个值都保留

// set(): 覆盖同名字段
formData.set('tag', 'backend');

console.log(formData.getAll('tag'));
// ['backend']  ✅ 之前的值全部被覆盖
```

使用原则:
- **append()**: 用于多值字段 (如标签、文件列表)
- **set()**: 用于单值字段 (如用户名、邮箱)
- **getAll()**: 获取所有同名字段的值 (返回数组)
- **get()**: 只获取第一个值 (返回字符串或 File)

---

**规则 5: 从现有表单创建 FormData 的便捷方式**

FormData 可以从 `<form>` 元素直接创建, 自动提取所有表单字段。

```javascript
// HTML 表单
<form id="myForm">
    <input type="text" name="username" value="Alice">
    <input type="email" name="email" value="alice@example.com">
    <input type="file" name="avatar">
    <select name="role">
        <option value="admin">管理员</option>
        <option value="user" selected>普通用户</option>
    </select>
    <input type="checkbox" name="terms" checked>
</form>

// 自动创建 FormData
const form = document.querySelector('#myForm');
const formData = new FormData(form);  // ✅ 自动提取所有字段

// 查看提取的数据
for (let [key, value] of formData.entries()) {
    console.log(key, value);
}
// username Alice
// email alice@example.com
// avatar File {...}
// role user
// terms on

// 可以继续添加额外字段
formData.append('timestamp', Date.now());
formData.append('source', 'web');
```

自动提取的规则:
- **input/textarea**: `name` 属性 → `value` 值
- **select**: `name` 属性 → 选中的 `value`
- **checkbox/radio**: 选中时添加, 未选中时不添加
- **file**: `name` 属性 → File 对象
- **disabled**: 被禁用的字段不会添加

---

**规则 6: FormData 的遍历与检查**

FormData 提供多种遍历和检查方法, 但不支持索引访问。

```javascript
const formData = new FormData();
formData.append('name', 'Alice');
formData.append('age', 25);
formData.append('tag', 'frontend');
formData.append('tag', 'javascript');

// 方法 1: entries() - 遍历所有键值对
for (let [key, value] of formData.entries()) {
    console.log(key, value);
}
// name Alice
// age 25
// tag frontend
// tag javascript

// 方法 2: keys() - 只遍历键
for (let key of formData.keys()) {
    console.log(key);
}
// name, age, tag, tag

// 方法 3: values() - 只遍历值
for (let value of formData.values()) {
    console.log(value);
}
// Alice, 25, frontend, javascript

// 方法 4: has() - 检查字段是否存在
console.log(formData.has('name'));  // true
console.log(formData.has('unknown'));  // false

// 方法 5: get() - 获取第一个值
console.log(formData.get('tag'));  // 'frontend' (第一个)

// 方法 6: getAll() - 获取所有值
console.log(formData.getAll('tag'));  // ['frontend', 'javascript']

// 方法 7: delete() - 删除字段
formData.delete('age');
console.log(formData.has('age'));  // false
```

注意事项:
- 无法用索引访问: `formData[0]` 无效
- 无法用点语法: `formData.name` 无效
- 同名字段会重复出现: `entries()` 中每个值都是独立条目
- `get()` 只返回第一个值: 多值字段需要用 `getAll()`

---

**规则 7: 嵌套对象和数组的处理策略**

FormData 只支持扁平结构, 嵌套对象需要手动序列化。

```javascript
const data = {
    name: 'Alice',
    profile: {
        age: 25,
        city: 'Beijing',
        hobbies: ['coding', 'reading']
    },
    tags: ['frontend', 'javascript']
};

const formData = new FormData();

// ✅ 策略 1: JSON 序列化嵌套对象
formData.append('name', data.name);
formData.append('profile', JSON.stringify(data.profile));
// 后端需要解析: JSON.parse(profile)

// ✅ 策略 2: 扁平化字段
formData.append('name', data.name);
formData.append('profile.age', data.profile.age);
formData.append('profile.city', data.profile.city);
// 后端需要重组对象

// ✅ 策略 3: 数组逐个添加
data.tags.forEach(tag => {
    formData.append('tags', tag);
});
// 后端接收到: ['frontend', 'javascript']

// ✅ 策略 4: 嵌套数组也需要序列化
data.profile.hobbies.forEach(hobby => {
    formData.append('hobbies', hobby);
});
```

最佳实践:
- **简单字段**: 直接 `append()`
- **嵌套对象**: `JSON.stringify()` 后再 `append()`
- **数组**: 逐个 `append()` (使用相同字段名)
- **文件**: 直接 `append()` File 对象
- **混合数据**: 文本用 JSON, 文件用原始对象

---

**规则 8: 上传进度监听需要 XMLHttpRequest**

Fetch API 无法监听上传进度, 需要使用 XMLHttpRequest 配合 FormData。

```javascript
// ❌ Fetch API 无法监听上传进度
function uploadWithFetch(file) {
    const formData = new FormData();
    formData.append('file', file);

    return fetch('/api/upload', {
        method: 'POST',
        body: formData
    });
    // 无法知道上传进度
}

// ✅ XMLHttpRequest 可以监听上传进度
function uploadWithProgress(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // 监听上传进度
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                onProgress(percent, e.loaded, e.total);
            }
        };

        // 上传完成
        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(new Error(`Upload failed: ${xhr.status}`));
            }
        };

        // 网络错误
        xhr.onerror = () => reject(new Error('Network error'));

        // 上传中止
        xhr.onabort = () => reject(new Error('Upload aborted'));

        xhr.open('POST', '/api/upload');
        xhr.send(formData);
    });
}

// 使用示例
const file = document.querySelector('#file').files[0];
uploadWithProgress(file, (percent, loaded, total) => {
    console.log(`上传进度: ${percent.toFixed(2)}%`);
    console.log(`已上传: ${loaded} / ${total} 字节`);
    updateProgressBar(percent);
})
.then(response => {
    console.log('上传成功:', response);
})
.catch(error => {
    console.error('上传失败:', error);
});
```

为什么需要 XMLHttpRequest:
- Fetch API 设计: 不支持上传进度监听 (只支持下载进度)
- xhr.upload 对象: 提供 `onprogress` 事件
- 兼容性: XMLHttpRequest 在所有浏览器都支持
- 功能完整: 支持进度、中止、超时控制

---

**事故档案编号**: NETWORK-2024-1946
**影响范围**: FormData, multipart/form-data, 文件上传, 表单提交
**根本原因**: 试图用 JSON 序列化 File 对象导致数据丢失, Content-Type 设置错误
**学习成本**: 中 (需理解 HTTP 表单编码和二进制数据传输)

这是 JavaScript 世界第 146 次被记录的网络与数据事故。FormData 是浏览器提供的专用 API, 用于构建符合 `multipart/form-data` 格式的 HTTP 请求体。它不是普通的 JavaScript 对象, 无法被 JSON 序列化, 也不能用对象语法访问。File 对象和 Blob 对象无法通过 `JSON.stringify()` 序列化, 必须使用 FormData 传输。提交 FormData 时, **绝对不能** 手动设置 `Content-Type` 头, 必须让浏览器自动添加 `boundary` 参数。`append()` 允许同名字段多次添加, `set()` 会覆盖同名字段。FormData 可以从 `<form>` 元素自动创建。上传进度监听需要使用 XMLHttpRequest 而非 Fetch API。理解 FormData 的特殊性和 `multipart/form-data` 编码格式是正确处理文件上传的基础。

---
