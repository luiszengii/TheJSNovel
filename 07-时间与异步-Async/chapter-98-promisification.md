《第 98 次记录: 回调改造工程 —— 旧世界的 Promise 化》

---

## 遗留代码的困境

周五上午九点,你盯着屏幕上那段有 5 年历史的代码,深深叹了口气。

项目经理刚刚分配了一个任务:"把文件上传模块重构成 Promise,要和新的异步架构保持一致。" 但这个模块是用老式回调写的,而且被十几个地方调用:

```javascript
// 老代码:回调风格
function uploadFile(file, onProgress, callback) {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            onProgress(percentComplete);
        }
    });

    xhr.addEventListener('load', function() {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            callback(null, response); // 成功
        } else {
            callback(new Error('上传失败: ' + xhr.status)); // 失败
        }
    });

    xhr.addEventListener('error', function() {
        callback(new Error('网络错误'));
    });

    xhr.open('POST', '/api/upload');
    xhr.send(formData);
}

// 使用方式
uploadFile(
    file,
    function(percent) {
        console.log('进度:', percent + '%');
    },
    function(err, result) {
        if (err) {
            console.error('上传失败:', err);
        } else {
            console.log('上传成功:', result);
        }
    }
);
```

"这种 Node.js 错误优先回调的风格,"你想,"要怎么改成 Promise 呢?"

你搜索了一下,看到"Promisification"这个词——把回调风格的函数转换成 Promise。

"听起来很简单,"你自言自语,"把回调换成 resolve/reject 就行了。但进度回调怎么办?Promise 只能 resolve 一次..."

---

## 第一次 Promisify 尝试

上午十点,你开始动手改造。

"先从最简单的开始,"你想,"一个没有进度回调的版本。"

你写下新代码:

```javascript
function uploadFilePromise(file) {
    return new Promise(function(resolve, reject) {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();

        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                resolve(response); // 成功
            } else {
                reject(new Error('上传失败: ' + xhr.status)); // 失败
            }
        });

        xhr.addEventListener('error', function() {
            reject(new Error('网络错误'));
        });

        xhr.open('POST', '/api/upload');
        xhr.send(formData);
    });
}

// 使用
uploadFilePromise(file)
    .then(function(result) {
        console.log('上传成功:', result);
    })
    .catch(function(error) {
        console.error('上传失败:', error);
    });
```

"基本功能可以了,"你说,"但进度回调丢失了。这可是重要功能,用户需要看到上传进度..."

你陷入了沉思。

---

## 进度回调的困境

上午十一点,你开始思考如何保留进度回调。

"Promise 只能 resolve 一次,但进度会触发很多次,"你分析,"怎么办?"

你尝试了几种方案:

```javascript
// 方案 1: 传入进度回调函数(混合风格)
function uploadFilePromise(file, onProgress) {
    return new Promise(function(resolve, reject) {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable && onProgress) {
                const percentComplete = (e.loaded / e.total) * 100;
                onProgress(percentComplete); // 仍然用回调处理进度
            }
        });

        // ... 其他代码
    });
}

// 使用
uploadFilePromise(
    file,
    function(percent) {
        console.log('进度:', percent + '%');
    }
)
.then(function(result) {
    console.log('完成:', result);
});
```

"这能工作,但感觉不够优雅,"你皱眉,"一半 Promise 一半回调,混合风格..."

你又想到了另一个方案:

```javascript
// 方案 2: 返回带有额外方法的 Promise
function uploadFilePromise(file) {
    let progressCallback;

    const promise = new Promise(function(resolve, reject) {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable && progressCallback) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressCallback(percentComplete);
            }
        });

        // ... 其他代码
    });

    // 给 Promise 添加自定义方法
    promise.onProgress = function(callback) {
        progressCallback = callback;
        return promise; // 支持链式调用
    };

    return promise;
}

// 使用
uploadFilePromise(file)
    .onProgress(function(percent) {
        console.log('进度:', percent + '%');
    })
    .then(function(result) {
        console.log('完成:', result);
    });
```

"这样看起来更好,"你说,"但这是标准做法吗?"

---

## 通用的 Promisify 工具

中午十二点,你开始研究通用的 promisify 模式。

"如果每个回调函数都手动包装,工作量太大了,"你想,"应该有通用工具。"

你查阅了 Node.js 的 `util.promisify` 文档,发现了标准模式:

```javascript
// 通用 promisify 函数
function promisify(fn) {
    return function(...args) {
        return new Promise(function(resolve, reject) {
            fn(...args, function(err, result) {
                if (err) {
                    reject(err);
                } else {
                    resolve(result);
                }
            });
        });
    };
}

// 使用
// 假设有一个老式回调函数
function readFileOld(path, callback) {
    setTimeout(function() {
        if (path.endsWith('.txt')) {
            callback(null, 'file content');
        } else {
            callback(new Error('Invalid file'));
        }
    }, 100);
}

// Promisify
const readFilePromise = promisify(readFileOld);

// 使用 Promise 版本
readFilePromise('test.txt')
    .then(function(content) {
        console.log('内容:', content);
    })
    .catch(function(error) {
        console.error('错误:', error);
    });
```

"这个工具很优雅,"你说,"但有个前提:回调函数必须遵循错误优先约定(error-first callback)。"

你测试了一些边界情况:

```javascript
// 测试 1: 多个参数的回调
function queryDatabase(sql, callback) {
    setTimeout(function() {
        callback(null, { rows: [], count: 0 });
    }, 100);
}

const queryPromise = promisify(queryDatabase);
queryPromise('SELECT * FROM users')
    .then(function(result) {
        console.log(result); // { rows: [], count: 0 }
    });

// 测试 2: 多个返回值
function getStats(callback) {
    setTimeout(function() {
        callback(null, 100, 200); // 两个返回值
    }, 100);
}

const getStatsPromise = promisify(getStats);
getStatsPromise()
    .then(function(result) {
        console.log(result); // 只能拿到第一个值: 100
        // 第二个值 200 丢失了!
    });
```

"原来 promisify 也有局限,"你发现,"如果回调有多个返回值,只能拿到第一个。"

---

## 改进的 Promisify 工具

下午两点,你开始改进 promisify 工具,支持多返回值:

```javascript
function promisifyMulti(fn) {
    return function(...args) {
        return new Promise(function(resolve, reject) {
            fn(...args, function(err, ...results) {
                if (err) {
                    reject(err);
                } else {
                    // 根据返回值数量决定 resolve 的内容
                    if (results.length === 0) {
                        resolve(undefined);
                    } else if (results.length === 1) {
                        resolve(results[0]);
                    } else {
                        resolve(results); // 多个返回值包装成数组
                    }
                }
            });
        });
    };
}

// 测试
function getStats(callback) {
    setTimeout(function() {
        callback(null, 100, 200, 300);
    }, 100);
}

const getStatsPromise = promisifyMulti(getStats);
getStatsPromise()
    .then(function(result) {
        console.log(result); // [100, 200, 300]
        const [count, sum, avg] = result;
        console.log('统计:', count, sum, avg);
    });
```

"这样就完整了,"你说,"可以处理多返回值的情况。"

---

## 批量 Promisify 整个模块

下午三点,你面临一个新问题:项目里有个旧的工具库,十几个函数都是回调风格。

"一个个手动 promisify 太麻烦了,"你想,"能不能批量转换?"

你写了一个批量工具:

```javascript
function promisifyAll(obj) {
    const promisified = {};

    for (const key in obj) {
        if (typeof obj[key] === 'function') {
            // 为每个函数创建 Promise 版本
            promisified[key] = promisify(obj[key]);
            // 保留原版本,添加 Async 后缀
            promisified[key + 'Async'] = promisify(obj[key]);
        }
    }

    return promisified;
}

// 使用
const fsOld = {
    readFile: function(path, callback) {
        setTimeout(() => callback(null, 'content'), 100);
    },
    writeFile: function(path, data, callback) {
        setTimeout(() => callback(null), 100);
    },
    deleteFile: function(path, callback) {
        setTimeout(() => callback(null), 100);
    }
};

const fs = promisifyAll(fsOld);

// 现在可以用 Promise 了
fs.readFileAsync('test.txt')
    .then(function(content) {
        return fs.writeFileAsync('output.txt', content.toUpperCase());
    })
    .then(function() {
        console.log('文件处理完成');
    });
```

"这样就方便多了,"你说,"整个模块一次性 promisify。"

但你马上发现了一个问题:

```javascript
// 问题:原对象的方法依赖 this
const logger = {
    prefix: '[LOG]',
    log: function(message, callback) {
        setTimeout(() => {
            console.log(this.prefix, message); // 依赖 this.prefix
            callback(null);
        }, 100);
    }
};

const loggerPromise = promisifyAll(logger);

loggerPromise.logAsync('Hello')
    .then(function() {
        console.log('完成');
    });
// 输出: undefined Hello
// this 丢失了!
```

"需要绑定 this,"你修复代码:

```javascript
function promisifyAll(obj) {
    const promisified = {};

    for (const key in obj) {
        if (typeof obj[key] === 'function') {
            promisified[key + 'Async'] = function(...args) {
                return new Promise(function(resolve, reject) {
                    obj[key].call(obj, ...args, function(err, result) {
                        if (err) reject(err);
                        else resolve(result);
                    });
                });
            };
        } else {
            // 保留非函数属性
            promisified[key] = obj[key];
        }
    }

    return promisified;
}
```

---

## 不符合约定的回调函数

下午四点,你遇到了一个棘手的问题。

项目里有个第三方库,它的回调不遵循错误优先约定:

```javascript
// 第三方库:成功优先约定(success-first)
function fetchData(url, successCallback, errorCallback) {
    setTimeout(function() {
        if (url.startsWith('http')) {
            successCallback({ data: 'content' }); // 成功回调
        } else {
            errorCallback(new Error('Invalid URL')); // 错误回调
        }
    }, 100);
}
```

"这种两个回调的风格,标准 promisify 不管用,"你说。

你写了一个自定义包装器:

```javascript
function fetchDataPromise(url) {
    return new Promise(function(resolve, reject) {
        fetchData(
            url,
            function(result) {
                resolve(result); // 成功回调 → resolve
            },
            function(error) {
                reject(error); // 错误回调 → reject
            }
        );
    });
}

// 使用
fetchDataPromise('https://api.example.com')
    .then(function(result) {
        console.log('数据:', result);
    })
    .catch(function(error) {
        console.error('错误:', error);
    });
```

你又遇到了更奇怪的:

```javascript
// jQuery 风格:链式回调
$.ajax({
    url: '/api/data',
    success: function(data) {
        console.log('成功:', data);
    },
    error: function(xhr, status, error) {
        console.error('失败:', error);
    }
});

// Promisify
function ajaxPromise(options) {
    return new Promise(function(resolve, reject) {
        $.ajax({
            ...options,
            success: resolve,
            error: function(xhr, status, error) {
                reject(new Error(error));
            }
        });
    });
}

// 使用
ajaxPromise({ url: '/api/data' })
    .then(function(data) {
        console.log('成功:', data);
    });
```

"不同的回调风格需要不同的包装方式,"你总结,"没有银弹,要根据具体情况处理。"

---

## 处理事件驱动的 API

下午五点,你遇到了最复杂的情况:事件驱动的 API。

```javascript
// 事件驱动的 WebSocket 连接
const ws = new WebSocket('ws://localhost:8080');

ws.onopen = function() {
    console.log('连接成功');
};

ws.onerror = function(error) {
    console.error('连接错误:', error);
};

ws.onmessage = function(event) {
    console.log('收到消息:', event.data);
};

ws.onclose = function() {
    console.log('连接关闭');
};
```

"这种多事件的 API 怎么 promisify?"你困惑。

你想了想,意识到:**连接建立可以用 Promise,但后续的消息需要用事件监听器**。

```javascript
function connectWebSocket(url) {
    return new Promise(function(resolve, reject) {
        const ws = new WebSocket(url);

        ws.onopen = function() {
            resolve(ws); // 连接成功,返回 WebSocket 实例
        };

        ws.onerror = function(error) {
            reject(error); // 连接失败
        };

        // 注意:连接成功后不能移除 onerror
        // 因为运行时还可能出错
    });
}

// 使用
connectWebSocket('ws://localhost:8080')
    .then(function(ws) {
        console.log('连接成功');

        // 后续用事件监听器
        ws.onmessage = function(event) {
            console.log('收到消息:', event.data);
        };

        ws.send('Hello Server');
    })
    .catch(function(error) {
        console.error('连接失败:', error);
    });
```

"Promise 适合一次性操作,事件适合持续监听,"你总结,"两者要结合使用,不能完全 promisify。"

---

## Promisify 的最佳实践

晚上七点,你整理了一天的收获。

你在笔记本上写下标题:"Promisification —— 旧代码改造指南"

### 核心洞察 #1: 标准 Promisify 模式

你写道:

"对于错误优先回调(error-first callback),使用标准 promisify:

```javascript
function promisify(fn) {
    return function(...args) {
        return new Promise(function(resolve, reject) {
            fn(...args, function(err, result) {
                if (err) reject(err);
                else resolve(result);
            });
        });
    };
}
```

适用条件:
- 回调函数遵循 `callback(err, result)` 约定
- 只有一个结果值
- 回调只调用一次

这是 Node.js `util.promisify` 的实现原理。"

### 核心洞察 #2: 处理多返回值

"如果回调有多个返回值,需要特殊处理:

```javascript
function promisifyMulti(fn) {
    return function(...args) {
        return new Promise(function(resolve, reject) {
            fn(...args, function(err, ...results) {
                if (err) reject(err);
                else if (results.length <= 1) resolve(results[0]);
                else resolve(results); // 多个值包装成数组
            });
        });
    };
}
```

使用时解构数组获取多个值。"

### 核心洞察 #3: 不同回调风格的处理

"不同库有不同的回调风格,需要定制包装:

- **错误优先**: `callback(err, result)` → 标准 promisify
- **成功优先**: `success(result), error(err)` → 自定义包装
- **jQuery 风格**: `{ success, error }` → 自定义包装
- **事件驱动**: 一次性操作用 Promise,持续监听用事件

没有通用工具,要根据实际情况编写包装器。"

### 核心洞察 #4: 批量 Promisify

"批量转换整个模块:

```javascript
function promisifyAll(obj) {
    const result = {};
    for (const key in obj) {
        if (typeof obj[key] === 'function') {
            result[key + 'Async'] = promisify(obj[key].bind(obj));
        }
    }
    return result;
}
```

注意绑定 this,避免上下文丢失。"

你合上笔记本,看着窗外的夜色。

"下周要学习 async/await 了,"你想,"但今天理解了 promisify 的本质——就是把回调函数的 resolve/reject 语义转换成 Promise。关键是要理解原回调的约定,然后正确映射到 Promise 的状态机上。"

---

## 知识总结

**规则 1: 标准 Promisify 模式**

将错误优先回调(error-first callback)转换为 Promise:

```javascript
function promisify(fn) {
    return function(...args) {
        return new Promise(function(resolve, reject) {
            fn(...args, function(err, result) {
                if (err) {
                    reject(err); // 错误 → reject
                } else {
                    resolve(result); // 成功 → resolve
                }
            });
        });
    };
}

// 使用
function readFile(path, callback) {
    // 异步读取文件
    setTimeout(function() {
        if (path) {
            callback(null, 'file content'); // 成功
        } else {
            callback(new Error('Invalid path')); // 失败
        }
    }, 100);
}

const readFilePromise = promisify(readFile);

readFilePromise('test.txt')
    .then(content => console.log(content))
    .catch(error => console.error(error));
```

适用条件:
- 回调函数遵循 `callback(err, result)` 约定
- 回调只调用一次
- 只有一个结果值

---

**规则 2: 处理多返回值的回调**

回调有多个返回值时,需要特殊处理:

```javascript
function promisifyMulti(fn) {
    return function(...args) {
        return new Promise(function(resolve, reject) {
            fn(...args, function(err, ...results) {
                if (err) {
                    reject(err);
                } else {
                    // 根据返回值数量决定 resolve 内容
                    if (results.length === 0) {
                        resolve(undefined);
                    } else if (results.length === 1) {
                        resolve(results[0]);
                    } else {
                        resolve(results); // 多个值包装成数组
                    }
                }
            });
        });
    };
}

// 使用
function getStats(callback) {
    callback(null, 100, 200, 300); // 三个返回值
}

const getStatsPromise = promisifyMulti(getStats);

getStatsPromise()
    .then(function(results) {
        const [count, sum, avg] = results; // 解构获取
        console.log(count, sum, avg);
    });
```

---

**规则 3: 批量 Promisify 整个模块**

批量转换对象的所有方法:

```javascript
function promisifyAll(obj) {
    const promisified = {};

    for (const key in obj) {
        if (typeof obj[key] === 'function') {
            // 创建 Promise 版本,添加 Async 后缀
            promisified[key + 'Async'] = function(...args) {
                return new Promise(function(resolve, reject) {
                    // 绑定原对象的 this
                    obj[key].call(obj, ...args, function(err, result) {
                        if (err) reject(err);
                        else resolve(result);
                    });
                });
            };
        } else {
            // 保留非函数属性
            promisified[key] = obj[key];
        }
    }

    return promisified;
}

// 使用
const fsOld = {
    readFile: function(path, cb) {
        setTimeout(() => cb(null, 'content'), 100);
    },
    writeFile: function(path, data, cb) {
        setTimeout(() => cb(null), 100);
    }
};

const fs = promisifyAll(fsOld);

// 使用 Promise 版本
fs.readFileAsync('test.txt')
    .then(content => fs.writeFileAsync('out.txt', content))
    .then(() => console.log('完成'));
```

注意:绑定 this 避免上下文丢失。

---

**规则 4: 不同回调风格的处理**

不同库有不同的回调约定,需要定制包装:

**风格 1: 成功优先(success-first)**
```javascript
// 原 API: successCallback, errorCallback
function fetchData(url, onSuccess, onError) {
    if (url.startsWith('http')) {
        onSuccess({ data: 'content' });
    } else {
        onError(new Error('Invalid URL'));
    }
}

// Promisify
function fetchDataPromise(url) {
    return new Promise(function(resolve, reject) {
        fetchData(url, resolve, reject);
    });
}
```

**风格 2: jQuery 风格**
```javascript
// 原 API: { success, error } 选项对象
$.ajax({
    url: '/api/data',
    success: function(data) {},
    error: function(xhr, status, error) {}
});

// Promisify
function ajaxPromise(options) {
    return new Promise(function(resolve, reject) {
        $.ajax({
            ...options,
            success: resolve,
            error: function(xhr, status, error) {
                reject(new Error(error));
            }
        });
    });
}
```

**风格 3: 事件驱动**
```javascript
// 原 API: 多个事件监听器
const ws = new WebSocket(url);
ws.onopen = function() {};
ws.onerror = function(error) {};

// Promisify: 一次性连接用 Promise,持续监听用事件
function connectWebSocket(url) {
    return new Promise(function(resolve, reject) {
        const ws = new WebSocket(url);
        ws.onopen = () => resolve(ws);
        ws.onerror = reject;
    });
}

// 使用
connectWebSocket('ws://localhost')
    .then(function(ws) {
        ws.onmessage = e => console.log(e.data); // 后续用事件
    });
```

---

**规则 5: 处理 this 上下文**

Promisify 时必须正确绑定 this:

```javascript
const logger = {
    prefix: '[LOG]',
    log: function(message, callback) {
        console.log(this.prefix, message); // 依赖 this
        callback(null);
    }
};

// ❌ 错误:this 丢失
const logPromise = promisify(logger.log);
logPromise('Hello'); // this.prefix 是 undefined

// ✅ 正确:绑定 this
const logPromise = promisify(logger.log.bind(logger));
logPromise('Hello'); // this.prefix 正确

// ✅ 或者在 promisify 内部绑定
function promisify(fn, context) {
    return function(...args) {
        return new Promise(function(resolve, reject) {
            fn.call(context, ...args, function(err, result) {
                if (err) reject(err);
                else resolve(result);
            });
        });
    };
}

const logPromise = promisify(logger.log, logger);
```

---

**规则 6: Node.js util.promisify**

Node.js 提供了内置的 promisify 工具:

```javascript
const util = require('util');
const fs = require('fs');

// 使用内置 promisify
const readFilePromise = util.promisify(fs.readFile);

readFilePromise('test.txt', 'utf8')
    .then(content => console.log(content))
    .catch(error => console.error(error));

// 或者批量 promisify
const fsPromises = require('fs').promises; // Node.js 10+ 内置
fsPromises.readFile('test.txt', 'utf8')
    .then(content => console.log(content));
```

自定义 promisify 行为:
```javascript
function customAsync(callback) {
    // 自定义函数
}

// 定义 promisify 行为
customAsync[util.promisify.custom] = function(...args) {
    return new Promise(function(resolve, reject) {
        // 自定义 Promise 化逻辑
    });
};

const customPromise = util.promisify(customAsync);
```

---

**规则 7: Promisify 的局限性**

Promise 适合一次性操作,不适合持续事件:

```javascript
// ❌ 不适合:多次触发的事件
// 进度事件会触发多次,但 Promise 只能 resolve 一次
function uploadFile(file) {
    return new Promise(function(resolve, reject) {
        xhr.upload.onprogress = function(e) {
            // 进度事件触发多次,无法用 Promise 表达
        };
        xhr.onload = () => resolve();
    });
}

// ✅ 正确:混合 Promise 和回调
function uploadFile(file, onProgress) {
    return new Promise(function(resolve, reject) {
        xhr.upload.onprogress = onProgress; // 进度用回调
        xhr.onload = () => resolve(); // 完成用 Promise
    });
}

// ✅ 或者返回增强的 Promise
function uploadFile(file) {
    let progressCallback;
    const promise = new Promise(function(resolve, reject) {
        xhr.upload.onprogress = e => progressCallback?.(e);
        xhr.onload = () => resolve();
    });
    promise.onProgress = cb => {
        progressCallback = cb;
        return promise;
    };
    return promise;
}
```

局限性:
- Promise 只能 resolve/reject 一次
- 不适合多次触发的事件
- 无法表达流式数据
- 无法取消已启动的操作

---

**规则 8: Promisify 的最佳实践**

选择合适的 promisify 策略:

**场景 1: 标准错误优先回调** → 使用 util.promisify 或标准模式
**场景 2: 自定义回调风格** → 手动包装
**场景 3: 整个模块** → promisifyAll
**场景 4: 事件驱动 API** → 一次性操作用 Promise,持续事件用回调/EventEmitter
**场景 5: 进度回调** → 混合模式或增强 Promise

实践建议:
- 优先使用库提供的 Promise 版本(如 fs.promises)
- 不要过度 promisify,保留原 API 供特殊场景使用
- 注意 this 绑定和多返回值处理
- 文档中说明 promisify 的行为和局限性

---

**事故档案编号**: ASYNC-2024-1898
**影响范围**: Promisification, 回调转 Promise, util.promisify
**根本原因**: 不理解回调与 Promise 的映射关系,导致 this 丢失或多返回值处理不当
**修复成本**: 低(正确包装回调)

这是 JavaScript 世界第 98 次被记录的 Promisification 事故。Promisify 将错误优先回调转换为 Promise:回调的 err 映射到 reject,result 映射到 resolve。标准模式适用于 `callback(err, result)` 约定。多返回值需要包装成数组或使用解构。批量 promisify 要注意绑定 this 避免上下文丢失。不同回调风格(成功优先、jQuery、事件驱动)需要定制包装。Promise 只能 resolve 一次,不适合多次触发的事件,需混合使用回调或增强 Promise。Node.js 提供 util.promisify 工具和 fs.promises 等内置 Promise API。理解回调与 Promise 的语义映射是正确 promisify 的关键。

---
