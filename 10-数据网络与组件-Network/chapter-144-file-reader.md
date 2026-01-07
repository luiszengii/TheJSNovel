《第 144 次记录: 文件读取的诡异失败 —— FileReader 的异步陷阱》

---

## 谜题现场

周二上午十一点，测试部门的小王走到你的工位旁边。

"有个很诡异的 bug，" 她说，"用户上传 Excel 文件时，有时候能成功，有时候就会失败。但同一个文件，重试几次又能成功了。"

你皱起眉头："'有时候'？能复现吗？"

"这就是奇怪的地方，" 小王打开她的笔记本，"我试了 20 次，失败了 3 次。但这 3 次失败没有任何规律——不是文件大小的问题，不是网络的问题，也不是浏览器版本的问题。"

你让她演示一遍。她选择了一个 2MB 的 Excel 文件，点击上传按钮。进度条走到 100%，然后...页面显示"上传失败：文件数据为空"。

"你看，" 小王说，"就是这样。同一个文件，现在再传一次..."

第二次上传成功了。

"这不科学，" 你说，"让我看看代码。"

你打开上传功能的源码，这是上个月实习生写的：

```javascript
function uploadExcel(file) {
    const reader = new FileReader();

    reader.readAsArrayBuffer(file);

    const data = reader.result;  // 读取结果

    if (!data) {
        showError('文件数据为空');
        return;
    }

    // 发送到服务器
    fetch('/api/upload', {
        method: 'POST',
        body: data
    });
}
```

"代码看起来没什么问题啊，" 你喃喃自语，"为什么会间歇性失败？"

---

## 线索收集

你决定在本地环境复现这个问题。

你准备了一个测试文件，在控制台里逐行执行代码：

```javascript
const file = document.querySelector('#fileInput').files[0];
const reader = new FileReader();

console.log('开始读取:', new Date().getTime());
reader.readAsArrayBuffer(file);
console.log('调用 readAsArrayBuffer 后:', new Date().getTime());

console.log('reader.result:', reader.result);
```

控制台输出：

```
开始读取: 1704096000123
调用 readAsArrayBuffer 后: 1704096000124
reader.result: null
```

"null？" 你困惑，"文件明明存在，为什么 result 是 null？"

你又测试了一个更详细的版本：

```javascript
const file = document.querySelector('#fileInput').files[0];
const reader = new FileReader();

console.log('readyState:', reader.readyState);  // 0 (EMPTY)
console.log('result:', reader.result);  // null

reader.readAsArrayBuffer(file);

console.log('readyState:', reader.readyState);  // 1 (LOADING)
console.log('result:', reader.result);  // null (还在读取)

// 等待 100ms 后
setTimeout(() => {
    console.log('readyState:', reader.readyState);  // 2 (DONE)
    console.log('result:', reader.result);  // ArrayBuffer(...)
}, 100);
```

输出结果让你恍然大悟：

```
readyState: 0
result: null
readyState: 1
result: null
--- 100ms 后 ---
readyState: 2
result: ArrayBuffer(2048576) {...}
```

"原来 FileReader 是异步的！" 你惊呼，"调用 `readAsArrayBuffer()` 后，result 不会立即可用，需要等待读取完成！"

你突然意识到原代码的问题所在：

```javascript
reader.readAsArrayBuffer(file);  // 启动异步读取

const data = reader.result;  // ❌ 此时 result 还是 null！

if (!data) {
    showError('文件数据为空');  // 总是会报错
}
```

"但为什么有时候能成功？" 你困惑，"按照这个逻辑，应该 100% 失败才对。"

---

## 假设验证

你开始建立新的假设。

"也许在某些情况下，文件读取非常快，" 你想，"快到在检查 result 之前就完成了？"

你写了一个测试脚本：

```javascript
// 测试 1: 小文件 (1KB)
const smallFile = new Blob(['x'.repeat(1024)]);
const reader1 = new FileReader();

console.time('小文件读取');
reader1.readAsArrayBuffer(smallFile);
console.log('立即检查:', reader1.result);  // null
console.timeEnd('小文件读取');

// 测试 2: 大文件 (10MB)
const largeFile = new Blob(['x'.repeat(10 * 1024 * 1024)]);
const reader2 = new FileReader();

console.time('大文件读取');
reader2.readAsArrayBuffer(largeFile);
console.log('立即检查:', reader2.result);  // null
console.timeEnd('大文件读取');
```

两次测试的结果都是 `null`。

"所以不是文件大小的问题，" 你总结，"那为什么用户报告'有时候能成功'？"

你又想到一个可能性——也许在某些极端情况下，JavaScript 的执行被意外延迟了，导致文件读取恰好在检查 result 之前完成。

你模拟了这种情况：

```javascript
const reader = new FileReader();

// 启动读取
reader.readAsArrayBuffer(file);

// 人为延迟 (模拟慢速设备或复杂计算)
const start = Date.now();
while (Date.now() - start < 50) {
    // 忙等待 50ms
}

// 50ms 后检查
console.log('延迟后检查:', reader.result);
```

这次，小文件的 result 变成了 `ArrayBuffer`！

"找到了！" 你兴奋，"在用户设备性能差或者浏览器繁忙时，JavaScript 主线程被阻塞，文件读取恰好完成了，所以 result 不是 null。这就是为什么'有时候能成功'！"

但这不是一个可靠的解决方案。你需要理解 FileReader 的正确使用方式。

---

## 真相揭晓

你打开 MDN 文档，仔细阅读 FileReader 的事件系统。

文档明确说明：**FileReader 是异步 API，必须通过事件监听读取结果**。

FileReader 提供了以下事件：

- `loadstart`: 读取开始
- `progress`: 读取进行中
- `load`: 读取成功
- `error`: 读取失败
- `abort`: 读取中止
- `loadend`: 读取结束 (无论成功或失败)

"原来如此，" 你恍然，"正确的做法是监听 `load` 事件！"

你重写了上传函数：

```javascript
// ❌ 错误的同步思维
function uploadExcelWrong(file) {
    const reader = new FileReader();
    reader.readAsArrayBuffer(file);

    const data = reader.result;  // null

    if (!data) {
        showError('文件数据为空');
        return;
    }

    fetch('/api/upload', { method: 'POST', body: data });
}

// ✅ 正确的异步处理
function uploadExcelCorrect(file) {
    const reader = new FileReader();

    // 监听加载完成事件
    reader.onload = (e) => {
        const data = e.target.result;

        if (!data) {
            showError('文件数据为空');
            return;
        }

        // 发送到服务器
        fetch('/api/upload', {
            method: 'POST',
            body: data
        });
    };

    // 监听错误事件
    reader.onerror = (e) => {
        showError('文件读取失败: ' + e.target.error);
    };

    // 启动读取
    reader.readAsArrayBuffer(file);
}
```

你测试了新代码，连续上传 50 次，全部成功。

"完美，" 你满意地点头，"100% 成功率。"

---

## 深入理解

下午三点，你决定系统地理解 FileReader 的工作机制。

你画了一个状态转换图：

```
FileReader 状态机：

EMPTY (0)
  ↓ readAsXXX()
LOADING (1)
  ↓ 读取完成
DONE (2)
```

你又测试了 FileReader 的不同读取方法：

```javascript
const file = new File(['Hello World'], 'test.txt', {
    type: 'text/plain'
});

// 方法 1: readAsText (读取为文本)
const reader1 = new FileReader();
reader1.onload = (e) => {
    console.log('Text:', e.target.result);
    // 'Hello World'
};
reader1.readAsText(file);

// 方法 2: readAsDataURL (读取为 Data URL)
const reader2 = new FileReader();
reader2.onload = (e) => {
    console.log('Data URL:', e.target.result);
    // 'data:text/plain;base64,SGVsbG8gV29ybGQ='
};
reader2.readAsDataURL(file);

// 方法 3: readAsArrayBuffer (读取为 ArrayBuffer)
const reader3 = new FileReader();
reader3.onload = (e) => {
    console.log('ArrayBuffer:', e.target.result);
    // ArrayBuffer(11)
};
reader3.readAsArrayBuffer(file);

// 方法 4: readAsBinaryString (读取为二进制字符串, 已废弃)
const reader4 = new FileReader();
reader4.onload = (e) => {
    console.log('Binary String:', e.target.result);
    // 'Hello World' (字节序列)
};
reader4.readAsBinaryString(file);
```

你又测试了进度监听：

```javascript
const largeFile = new Blob(['x'.repeat(10 * 1024 * 1024)]);  // 10MB
const reader = new FileReader();

reader.onloadstart = (e) => {
    console.log('开始读取');
};

reader.onprogress = (e) => {
    if (e.lengthComputable) {
        const percent = (e.loaded / e.total * 100).toFixed(2);
        console.log(`进度: ${percent}%`);
    }
};

reader.onload = (e) => {
    console.log('读取完成, 数据大小:', e.target.result.byteLength);
};

reader.onerror = (e) => {
    console.error('读取失败:', e.target.error);
};

reader.onloadend = (e) => {
    console.log('读取结束 (成功或失败)');
};

reader.readAsArrayBuffer(largeFile);
```

输出结果：

```
开始读取
进度: 25.00%
进度: 50.00%
进度: 75.00%
进度: 100.00%
读取完成, 数据大小: 10485760
读取结束 (成功或失败)
```

"FileReader 提供了完整的事件系统，" 你总结，"可以监听读取的每个阶段。"

---

## 最佳实践

你创建了一个封装类，统一处理文件读取的各种场景：

```javascript
class FileReaderHelper {
    // 读取文本文件
    static readAsText(file, encoding = 'UTF-8') {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e.target.error);

            reader.readAsText(file, encoding);
        });
    }

    // 读取为 ArrayBuffer
    static readAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e.target.error);

            reader.readAsArrayBuffer(file);
        });
    }

    // 读取为 Data URL (用于预览)
    static readAsDataURL(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e.target.error);

            reader.readAsDataURL(file);
        });
    }

    // 带进度监听的读取
    static readWithProgress(file, onProgress) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onprogress = (e) => {
                if (e.lengthComputable && onProgress) {
                    const percent = (e.loaded / e.total) * 100;
                    onProgress(percent, e.loaded, e.total);
                }
            };

            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e.target.error);

            reader.readAsArrayBuffer(file);
        });
    }

    // 分块读取大文件
    static async readInChunks(file, chunkSize = 1024 * 1024, onChunk) {
        let offset = 0;

        while (offset < file.size) {
            const chunk = file.slice(offset, offset + chunkSize);
            const data = await FileReaderHelper.readAsArrayBuffer(chunk);

            if (onChunk) {
                await onChunk(data, offset, file.size);
            }

            offset += chunkSize;
        }
    }
}
```

使用示例：

```javascript
// 示例 1: 读取文本文件
async function handleTextFile(file) {
    try {
        const text = await FileReaderHelper.readAsText(file);
        console.log('文件内容:', text);
    } catch (error) {
        console.error('读取失败:', error);
    }
}

// 示例 2: 图片预览
async function previewImage(file) {
    try {
        const dataURL = await FileReaderHelper.readAsDataURL(file);
        document.querySelector('#preview').src = dataURL;
    } catch (error) {
        console.error('预览失败:', error);
    }
}

// 示例 3: 带进度的文件上传
async function uploadWithProgress(file) {
    try {
        const data = await FileReaderHelper.readWithProgress(
            file,
            (percent, loaded, total) => {
                console.log(`上传进度: ${percent.toFixed(2)}%`);
                updateProgressBar(percent);
            }
        );

        await fetch('/api/upload', {
            method: 'POST',
            body: data
        });

        console.log('上传成功');
    } catch (error) {
        console.error('上传失败:', error);
    }
}

// 示例 4: 分块处理大文件
async function processLargeFile(file) {
    await FileReaderHelper.readInChunks(
        file,
        1024 * 1024,  // 1MB 每块
        async (chunk, offset, total) => {
            console.log(`处理块: ${offset} / ${total}`);
            await processChunk(chunk);
        }
    );

    console.log('处理完成');
}
```

---

## 常见陷阱

你整理了 FileReader 使用中的常见错误：

**陷阱 1: 同步思维**

```javascript
// ❌ 错误：把异步 API 当同步使用
const reader = new FileReader();
reader.readAsText(file);
console.log(reader.result);  // null

// ✅ 正确：使用事件或 Promise
const reader = new FileReader();
reader.onload = (e) => {
    console.log(e.target.result);  // 正确的结果
};
reader.readAsText(file);
```

**陷阱 2: 忘记错误处理**

```javascript
// ❌ 错误：没有监听 error 事件
const reader = new FileReader();
reader.onload = (e) => {
    console.log(e.target.result);
};
reader.readAsText(file);  // 如果文件不可读，没有任何提示

// ✅ 正确：添加错误处理
const reader = new FileReader();
reader.onload = (e) => {
    console.log(e.target.result);
};
reader.onerror = (e) => {
    console.error('读取失败:', e.target.error);
};
reader.readAsText(file);
```

**陷阱 3: 重用 FileReader 实例**

```javascript
// ❌ 错误：同一个 reader 连续读取多个文件
const reader = new FileReader();

files.forEach(file => {
    reader.onload = (e) => console.log(e.target.result);
    reader.readAsText(file);  // 只有最后一个文件会触发 onload
});

// ✅ 正确：每个文件创建新的 reader
files.forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => console.log(e.target.result);
    reader.readAsText(file);
});
```

**陷阱 4: 内存泄漏 (Data URL)**

```javascript
// ❌ 错误：Data URL 导致内存泄漏
const reader = new FileReader();
reader.onload = (e) => {
    img.src = e.target.result;  // Data URL 会一直占用内存
};
reader.readAsDataURL(largeFile);

// ✅ 正确：使用 Blob URL (更高效)
const url = URL.createObjectURL(file);
img.src = url;
img.onload = () => {
    URL.revokeObjectURL(url);  // 释放内存
};
```

**陷阱 5: 大文件阻塞**

```javascript
// ❌ 错误：一次性读取超大文件
const reader = new FileReader();
reader.onload = (e) => {
    const data = e.target.result;  // 可能占用几百 MB 内存
    processData(data);
};
reader.readAsArrayBuffer(hugeFile);  // 10GB 文件

// ✅ 正确：分块读取
async function readLargeFile(file) {
    const chunkSize = 1024 * 1024;  // 1MB
    let offset = 0;

    while (offset < file.size) {
        const chunk = file.slice(offset, offset + chunkSize);
        const reader = new FileReader();

        const data = await new Promise((resolve, reject) => {
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e.target.error);
            reader.readAsArrayBuffer(chunk);
        });

        await processChunk(data);
        offset += chunkSize;
    }
}
```

---

## 修复验证

下午五点，你将修复后的代码部署到测试环境。

小王进行了完整的回归测试：

- 小文件 (1KB): 100 次上传，100% 成功
- 中等文件 (2MB): 100 次上传，100% 成功
- 大文件 (10MB): 50 次上传，100% 成功
- 超大文件 (50MB): 20 次上传，100% 成功

"完美！" 小王说，"之前那个间歇性失败完全消失了。"

你又测试了边缘情况：

```javascript
// 测试 1: 空文件
const emptyFile = new File([], 'empty.txt');
const data1 = await FileReaderHelper.readAsText(emptyFile);
console.log('空文件:', data1);  // '' (空字符串)

// 测试 2: 特殊字符
const specialFile = new File(['你好 World 😀'], 'special.txt');
const data2 = await FileReaderHelper.readAsText(specialFile);
console.log('特殊字符:', data2);  // '你好 World 😀'

// 测试 3: 二进制文件
const binaryFile = new File([new Uint8Array([0xFF, 0xFE])], 'binary.bin');
const data3 = await FileReaderHelper.readAsArrayBuffer(binaryFile);
console.log('二进制:', new Uint8Array(data3));  // [255, 254]
```

所有测试都通过了。

"这次 bug 的根因很简单，" 你在团队会议上总结，"但很有代表性——把异步 API 当成同步使用。FileReader 是完全异步的，必须通过事件或 Promise 获取结果。直接访问 `reader.result` 在读取启动后会返回 null，只有在极少数情况下（设备慢、主线程阻塞）才会碰巧读取完成，这就是为什么出现间歇性失败。"

---

## 知识总结

**规则 1: FileReader 是完全异步的 API**

FileReader 的所有读取方法 (`readAsText`, `readAsArrayBuffer`, `readAsDataURL`) 都是异步的，必须通过事件监听获取结果。

```javascript
// ❌ 错误：同步访问
const reader = new FileReader();
reader.readAsText(file);
const data = reader.result;  // null (读取未完成)

// ✅ 正确：事件监听
const reader = new FileReader();
reader.onload = (e) => {
    const data = e.target.result;  // 正确的结果
};
reader.readAsText(file);

// ✅ 正确：Promise 封装
function readFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(e.target.error);
        reader.readAsText(file);
    });
}
```

核心原因：
- 文件读取是 I/O 操作，需要时间
- JavaScript 是单线程，不能阻塞主线程等待读取
- 必须通过事件机制异步通知读取完成

---

**规则 2: FileReader 的状态机制**

FileReader 有三个状态 (readyState)：

```javascript
const reader = new FileReader();

console.log(reader.readyState);  // 0 (EMPTY)
console.log(reader.EMPTY);  // 0
console.log(reader.LOADING);  // 1
console.log(reader.DONE);  // 2

reader.readAsText(file);
console.log(reader.readyState);  // 1 (LOADING)

reader.onload = (e) => {
    console.log(reader.readyState);  // 2 (DONE)
};
```

状态转换：
- **EMPTY (0)**: 初始状态，未开始读取
- **LOADING (1)**: 正在读取中
- **DONE (2)**: 读取完成 (成功或失败)

注意：
- `result` 只在 DONE 状态才有值
- 在 LOADING 状态访问 `result` 返回 null
- 状态不可逆，只能从 EMPTY → LOADING → DONE

---

**规则 3: FileReader 的事件系统**

FileReader 提供了完整的事件生命周期：

```javascript
const reader = new FileReader();

// 读取开始
reader.onloadstart = (e) => {
    console.log('开始读取');
};

// 读取进行中
reader.onprogress = (e) => {
    if (e.lengthComputable) {
        const percent = (e.loaded / e.total) * 100;
        console.log(`进度: ${percent}%`);
    }
};

// 读取成功
reader.onload = (e) => {
    console.log('读取成功:', e.target.result);
};

// 读取失败
reader.onerror = (e) => {
    console.error('读取失败:', e.target.error);
};

// 读取中止
reader.onabort = (e) => {
    console.log('读取被中止');
};

// 读取结束 (成功或失败)
reader.onloadend = (e) => {
    console.log('读取结束');
};

reader.readAsText(file);
```

事件顺序：
1. `loadstart` (开始)
2. `progress` (多次, 可选)
3. `load` / `error` / `abort` (三选一)
4. `loadend` (结束)

最佳实践：
- 必须监听 `onload` 获取结果
- 应该监听 `onerror` 处理错误
- 可选监听 `onprogress` 显示进度

---

**规则 4: 四种读取方法的选择**

FileReader 提供四种读取方法：

```javascript
const file = new File(['Hello World'], 'test.txt');

// 方法 1: readAsText (读取为文本)
// 适用场景: TXT, JSON, CSV, HTML 等文本文件
const reader1 = new FileReader();
reader1.onload = (e) => {
    console.log(e.target.result);  // 'Hello World' (字符串)
};
reader1.readAsText(file, 'UTF-8');  // 第二参数：字符编码

// 方法 2: readAsArrayBuffer (读取为 ArrayBuffer)
// 适用场景: 二进制处理, 加密, 压缩, 网络传输
const reader2 = new FileReader();
reader2.onload = (e) => {
    console.log(e.target.result);  // ArrayBuffer(11)
};
reader2.readAsArrayBuffer(file);

// 方法 3: readAsDataURL (读取为 Data URL)
// 适用场景: 图片预览, 小文件嵌入
const reader3 = new FileReader();
reader3.onload = (e) => {
    console.log(e.target.result);
    // 'data:text/plain;base64,SGVsbG8gV29ybGQ='
    img.src = e.target.result;  // 可直接用于 img.src
};
reader3.readAsDataURL(file);

// 方法 4: readAsBinaryString (已废弃, 不推荐)
// 使用 readAsArrayBuffer + TextDecoder 替代
```

选择原则：
- **文本内容** → `readAsText`
- **二进制处理** → `readAsArrayBuffer`
- **图片预览** (小文件) → `readAsDataURL`
- **图片预览** (大文件) → `URL.createObjectURL` (更高效)

---

**规则 5: 大文件处理的分块策略**

大文件应该分块读取，避免内存占用过高：

```javascript
// ❌ 错误：一次性读取大文件
async function readLargeFileWrong(file) {
    const reader = new FileReader();
    const data = await new Promise(resolve => {
        reader.onload = (e) => resolve(e.target.result);
        reader.readAsArrayBuffer(file);  // 可能占用 GB 级内存
    });
    return data;
}

// ✅ 正确：分块读取
async function readLargeFileCorrect(file, chunkSize = 1024 * 1024) {
    const chunks = [];
    let offset = 0;

    while (offset < file.size) {
        // 使用 File.slice 切片
        const chunk = file.slice(offset, offset + chunkSize);

        // 读取当前块
        const reader = new FileReader();
        const data = await new Promise((resolve, reject) => {
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e.target.error);
            reader.readAsArrayBuffer(chunk);
        });

        chunks.push(data);
        offset += chunkSize;
    }

    // 合并所有块
    const totalLength = chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
    const result = new Uint8Array(totalLength);
    let position = 0;

    chunks.forEach(chunk => {
        result.set(new Uint8Array(chunk), position);
        position += chunk.byteLength;
    });

    return result.buffer;
}
```

分块策略的优势：
- 内存占用可控 (只保留当前块)
- 可以显示进度
- 可以随时中止
- 适用于流式处理

---

**规则 6: FileReader vs Blob URL 的选择**

图片预览有两种方式，根据文件大小选择：

```javascript
// 方式 1: FileReader.readAsDataURL (适合小文件)
// 优点: 无需手动释放, 可脱机使用
// 缺点: base64 编码增大 33%, 内存占用高
async function previewSmallImage(file) {
    if (file.size > 1024 * 1024) {  // 大于 1MB
        console.warn('文件过大, 建议使用 Blob URL');
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        img.src = e.target.result;
        // Data URL 会保留在内存中, 直到 img.src 被替换
    };
    reader.readAsDataURL(file);
}

// 方式 2: URL.createObjectURL (适合大文件)
// 优点: 无编码开销, 内存高效
// 缺点: 需要手动释放, 不能脱机使用
function previewLargeImage(file) {
    const url = URL.createObjectURL(file);

    img.src = url;

    // 图片加载完成后释放 URL
    img.onload = () => {
        URL.revokeObjectURL(url);
    };
}
```

选择原则：
- **文件 <1MB** → `readAsDataURL` (简单方便)
- **文件 >1MB** → `URL.createObjectURL` (内存高效)
- **需要 base64** → `readAsDataURL` (如嵌入 HTML)
- **仅预览** → `URL.createObjectURL` (性能更好)

---

**规则 7: 错误处理与中止机制**

FileReader 的错误处理和中止操作：

```javascript
const reader = new FileReader();

// 错误处理
reader.onerror = (e) => {
    const error = e.target.error;

    console.error('错误类型:', error.name);
    console.error('错误信息:', error.message);

    // 常见错误类型
    // NotFoundError: 文件不存在
    // NotReadableError: 文件不可读 (权限问题)
    // SecurityError: 安全限制
    // AbortError: 读取被中止
};

// 中止读取
reader.onloadstart = () => {
    console.log('开始读取...');

    // 5 秒后中止
    setTimeout(() => {
        if (reader.readyState === FileReader.LOADING) {
            reader.abort();  // 中止读取
            console.log('读取被中止');
        }
    }, 5000);
};

reader.onabort = () => {
    console.log('读取已中止');
};

reader.readAsArrayBuffer(largeFile);
```

中止机制：
- 调用 `reader.abort()` 中止读取
- 触发 `onabort` 事件
- `readyState` 变为 DONE
- `result` 保持为 null

---

**规则 8: Promise 封装最佳实践**

将 FileReader 封装为 Promise，简化异步处理：

```javascript
class FileReaderPromise {
    // 基础封装
    static read(file, method = 'readAsArrayBuffer') {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e.target.error);

            reader[method](file);
        });
    }

    // 带进度的封装
    static readWithProgress(file, onProgress, method = 'readAsArrayBuffer') {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onprogress = (e) => {
                if (e.lengthComputable && onProgress) {
                    onProgress({
                        percent: (e.loaded / e.total) * 100,
                        loaded: e.loaded,
                        total: e.total
                    });
                }
            };

            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e.target.error);

            reader[method](file);
        });
    }

    // 可中止的封装
    static readAbortable(file, signal, method = 'readAsArrayBuffer') {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            // 监听中止信号
            signal.addEventListener('abort', () => {
                reader.abort();
                reject(new DOMException('Aborted', 'AbortError'));
            });

            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e.target.error);

            reader[method](file);
        });
    }
}

// 使用示例
async function example() {
    // 基础使用
    const data = await FileReaderPromise.read(file, 'readAsText');

    // 带进度
    const data2 = await FileReaderPromise.readWithProgress(
        file,
        ({ percent, loaded, total }) => {
            console.log(`${percent}% (${loaded}/${total})`);
        }
    );

    // 可中止
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 5000);  // 5 秒后中止

    try {
        const data3 = await FileReaderPromise.readAbortable(
            file,
            controller.signal
        );
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('读取被中止');
        }
    }
}
```

---

**事故档案编号**: NETWORK-2024-1944
**影响范围**: FileReader, File API, 异步编程, 间歇性 bug
**根本原因**: 将异步 API 当作同步使用，直接访问未完成的 reader.result
**学习成本**: 低 (理解异步机制后容易掌握)

这是 JavaScript 世界第 144 次被记录的网络与数据事故。FileReader 是完全异步的 API，所有读取方法 (`readAsText`, `readAsArrayBuffer`, `readAsDataURL`) 都不会立即返回结果，必须通过 `onload` 事件监听获取读取结果。直接访问 `reader.result` 在读取启动后会返回 null，只有在极少数情况下（设备慢导致 JavaScript 执行延迟）才会碰巧在读取完成后访问，从而导致间歇性失败。FileReader 有三个状态 (EMPTY, LOADING, DONE) 和完整的事件系统 (loadstart, progress, load, error, abort, loadend)。正确的使用方式是通过 Promise 封装或直接监听事件，避免同步思维。大文件应使用 `File.slice()` 分块读取，避免内存占用过高。理解 FileReader 的异步本质是正确使用文件 API 的基础。

---
