《第 96 次记录: 错误吞噬事故 —— 静默失败的噩梦》

---

## 用户数据丢失的紧急事故

周三上午九点,你被一通紧急电话叫醒。

"生产环境出大问题了!"运维工程师老张的声音带着焦急,"用户报告说他们提交的表单数据全部丢失,但系统没有任何错误提示。已经有 50 多个用户投诉了。"

你立刻打开电脑,切换到生产环境的日志监控面板。奇怪的是,错误日志里一片空白——没有任何异常记录。

"怎么可能..."你喃喃自语,"数据丢失了,但系统却认为一切正常?"

你快速查看了前端代码。表单提交使用的是你上周刚重构的 Promise 链:

```javascript
function submitForm(formData) {
    return validateForm(formData)
        .then(function(validData) {
            return saveToDatabase(validData);
        })
        .then(function(result) {
            return sendConfirmationEmail(result.userId);
        })
        .then(function() {
            showSuccessMessage('提交成功');
        });
}
```

代码看起来很干净,很标准。但用户的数据确实丢失了,而且系统还显示"提交成功"。

"一定是哪里出错了,但错误被吞掉了,"你意识到问题的严重性,"这是最危险的 bug——静默失败。"

---

## 追踪被吞噬的错误

上午十点,你开始在本地环境复现问题。

你故意让数据库操作失败,看看会发生什么:

```javascript
function saveToDatabase(data) {
    return new Promise(function(resolve, reject) {
        // 模拟数据库错误
        setTimeout(function() {
            reject(new Error('数据库连接失败'));
        }, 100);
    });
}

// 提交表单
submitForm({ name: '张三', email: 'test@example.com' });
```

你盯着屏幕,等待错误提示。但什么都没发生——没有错误信息,没有提示框,控制台也一片空白。

"错误去哪了?"你困惑不已。

你打开 Chrome DevTools,切换到 Console 面板,看到了一行警告:

```
Uncaught (in promise) Error: 数据库连接失败
```

"原来在这里!"你说,"但为什么用户看不到任何提示?"

你仔细检查代码,突然意识到一个致命问题:**Promise 链没有 catch,错误被浏览器吞掉了**。

```javascript
function submitForm(formData) {
    return validateForm(formData)
        .then(function(validData) {
            return saveToDatabase(validData);
        })
        .then(function(result) {
            return sendConfirmationEmail(result.userId);
        })
        .then(function() {
            showSuccessMessage('提交成功'); // ← 这里会执行吗?
        });
    // ← 缺少 .catch()!
}
```

"天哪,"你拍了下桌子,"如果中间任何一步失败,后续的 then 都会被跳过,但因为没有 catch,错误就消失了。"

更糟糕的是,你发现了另一个问题:

```javascript
.then(function() {
    showSuccessMessage('提交成功'); // 这个函数也可能抛出错误!
})
```

"如果 `showSuccessMessage` 抛出错误,整个 Promise 链就崩溃了,但没有任何地方捕获这个错误。"

---

## 错误传播的真相

上午十一点,你决定深入理解 Promise 的错误传播机制。

你写了一系列测试代码:

```javascript
// 测试 1: 错误从哪里开始传播?
Promise.resolve(1)
    .then(function(value) {
        console.log('步骤 1:', value);
        return value + 1;
    })
    .then(function(value) {
        console.log('步骤 2:', value);
        throw new Error('步骤 2 出错'); // 抛出错误
    })
    .then(function(value) {
        console.log('步骤 3:', value); // 会执行吗?
    })
    .then(function(value) {
        console.log('步骤 4:', value); // 会执行吗?
    });
```

控制台输出:

```
步骤 1: 1
步骤 2: 2
Uncaught (in promise) Error: 步骤 2 出错
```

"所以步骤 3 和步骤 4 都被跳过了,"你说,"错误发生后,所有后续的 then 都不会执行。"

你添加了 catch:

```javascript
Promise.resolve(1)
    .then(function(value) {
        console.log('步骤 1:', value);
        return value + 1;
    })
    .then(function(value) {
        console.log('步骤 2:', value);
        throw new Error('步骤 2 出错');
    })
    .then(function(value) {
        console.log('步骤 3:', value); // 被跳过
    })
    .catch(function(error) {
        console.log('捕获错误:', error.message);
    })
    .then(function(value) {
        console.log('步骤 4:', value); // 会执行吗?
    });
```

输出:

```
步骤 1: 1
步骤 2: 2
捕获错误: 步骤 2 出错
步骤 4: undefined
```

"等等..."你的眼睛亮了,"catch 之后的 then 居然还能执行?"

你画了一张图:

```
.then(步骤1) ──> 成功
.then(步骤2) ──> 抛出错误
.then(步骤3) ──> 跳过 ─┐
.then(步骤4) ──> 跳过  │
.catch()    ◄──────────┘ 捕获错误
.then(步骤5) ──> 恢复执行!
```

"原来 catch 不仅捕获错误,还能让 Promise 链恢复执行!"你恍然大悟。

---

## catch 的位置决定一切

中午十二点,你开始测试 catch 放在不同位置的效果。

```javascript
// 场景 1: catch 在最后
function scenario1() {
    return step1()
        .then(step2)
        .then(step3)
        .catch(function(error) {
            console.log('统一错误处理:', error.message);
        });
}

// 场景 2: catch 在中间
function scenario2() {
    return step1()
        .then(step2)
        .catch(function(error) {
            console.log('捕获 step2 的错误:', error.message);
            return 'fallback'; // 返回备用值
        })
        .then(step3) // 会继续执行
        .catch(function(error) {
            console.log('捕获 step3 的错误:', error.message);
        });
}

// 场景 3: 多个 catch
function scenario3() {
    return step1()
        .catch(function(error) {
            console.log('step1 失败:', error.message);
            throw error; // 重新抛出
        })
        .then(step2)
        .catch(function(error) {
            console.log('step2 失败:', error.message);
            throw error;
        })
        .then(step3)
        .catch(function(error) {
            console.log('最终错误处理:', error.message);
        });
}
```

你测试了这三种场景,发现了关键规律:

"catch 的位置决定了它能捕获哪些错误,"你总结,"而且 catch 可以让链条恢复,继续执行后续的 then。"

但你马上又发现了一个陷阱。

---

## catch 里的错误会怎样?

下午两点,你测试了一个更复杂的场景。

"如果 catch 里的代码也出错了呢?"你好奇。

```javascript
Promise.reject(new Error('初始错误'))
    .catch(function(error) {
        console.log('捕获错误:', error.message);
        throw new Error('catch 里的新错误'); // catch 里抛出新错误
    })
    .then(function() {
        console.log('这里会执行吗?'); // 不会执行
    })
    .catch(function(error) {
        console.log('捕获 catch 里的错误:', error.message);
    });
```

输出:

```
捕获错误: 初始错误
捕获 catch 里的错误: catch 里的新错误
```

"所以 catch 里的错误也会向下传播,"你说,"需要另一个 catch 来捕获。"

你又测试了一个更诡异的情况:

```javascript
Promise.reject(new Error('错误'))
    .catch(function(error) {
        console.log('第一个 catch:', error.message);
        // 没有 throw,没有 return
    })
    .catch(function(error) {
        console.log('第二个 catch:', error); // 会执行吗?
    })
    .then(function(value) {
        console.log('then:', value); // 会执行吗?
    });
```

输出:

```
第一个 catch: 错误
then: undefined
```

"等等..."你困惑了,"第二个 catch 没有执行,但 then 执行了?"

你仔细思考了一会儿,突然明白了:**catch 成功处理错误后,Promise 链变成 fulfilled 状态,所以走 then 而不是 catch**。

"除非 catch 里抛出新错误,否则链条会恢复正常,"你总结。

---

## finally 的发现

下午三点,你想起文档里提到过一个叫 `finally` 的方法。

"finally 和 catch 有什么区别?"你搜索文档。

你写了测试代码:

```javascript
function testFinally(shouldFail) {
    return new Promise(function(resolve, reject) {
        setTimeout(function() {
            if (shouldFail) {
                reject(new Error('操作失败'));
            } else {
                resolve('操作成功');
            }
        }, 100);
    })
    .then(function(result) {
        console.log('成功:', result);
        return result;
    })
    .catch(function(error) {
        console.log('失败:', error.message);
        throw error; // 重新抛出
    })
    .finally(function() {
        console.log('无论成功失败都会执行');
        // finally 里没有参数
    });
}

// 测试成功情况
testFinally(false);
// 输出:
// 成功: 操作成功
// 无论成功失败都会执行

// 测试失败情况
testFinally(true);
// 输出:
// 失败: 操作失败
// 无论成功失败都会执行
// Uncaught (in promise) Error: 操作失败
```

"原来 finally 的特点是:"你总结:

1. **无论成功失败都执行**
2. **没有参数**(不知道是成功还是失败)
3. **不改变 Promise 的值**(透传结果或错误)
4. **用于清理工作**(关闭连接、隐藏 loading 等)

你重写了表单提交函数:

```javascript
function submitForm(formData) {
    showLoading(); // 显示加载状态

    return validateForm(formData)
        .then(function(validData) {
            return saveToDatabase(validData);
        })
        .then(function(result) {
            return sendConfirmationEmail(result.userId);
        })
        .then(function() {
            showSuccessMessage('提交成功');
        })
        .catch(function(error) {
            showErrorMessage(error.message);
            console.error('表单提交失败:', error);
        })
        .finally(function() {
            hideLoading(); // 无论成功失败都隐藏加载状态
        });
}
```

"这样就完美了,"你说,"loading 状态一定会被清理,不管成功还是失败。"

---

## 错误恢复的艺术

下午四点,你开始研究如何从错误中恢复。

"有些错误是可以恢复的,"你想,"比如网络超时可以重试,某个服务失败可以用备选方案。"

你写了一个自动重试的函数:

```javascript
function fetchWithRetry(url, maxRetries = 3) {
    function attempt(retriesLeft) {
        return fetch(url)
            .catch(function(error) {
                if (retriesLeft > 0) {
                    console.log(`请求失败,还剩 ${retriesLeft} 次重试机会`);
                    return attempt(retriesLeft - 1); // 递归重试
                }
                throw error; // 重试次数用完,抛出错误
            });
    }

    return attempt(maxRetries);
}

// 使用
fetchWithRetry('https://api.example.com/data')
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        console.log('获取数据成功:', data);
    })
    .catch(function(error) {
        console.error('重试 3 次后仍然失败:', error);
    });
```

你又写了一个备选方案的例子:

```javascript
function loadUserAvatar(userId) {
    return fetchFromCDN(userId)
        .catch(function(error) {
            console.warn('CDN 加载失败,尝试主服务器');
            return fetchFromMainServer(userId);
        })
        .catch(function(error) {
            console.warn('主服务器加载失败,使用默认头像');
            return getDefaultAvatar();
        });
}
```

"这就是错误恢复的优雅方式,"你说,"catch 不仅用于报错,还能提供备选方案。"

---

## 异步函数里的 try-catch 陷阱

下午五点,你突然想到一个问题。

"如果在 then 里使用 try-catch 会怎样?"你测试:

```javascript
Promise.resolve(1)
    .then(function(value) {
        try {
            throw new Error('then 里的错误');
        } catch (error) {
            console.log('try-catch 捕获:', error.message);
        }
    })
    .then(function() {
        console.log('继续执行'); // 会执行
    });

// 输出:
// try-catch 捕获: then 里的错误
// 继续执行
```

"try-catch 在 then 里可以用,"你说,"但有个限制..."

你又测试了异步错误:

```javascript
Promise.resolve(1)
    .then(function(value) {
        try {
            setTimeout(function() {
                throw new Error('异步错误'); // try-catch 捕获不到!
            }, 0);
        } catch (error) {
            console.log('try-catch 捕获:', error.message);
        }
    })
    .then(function() {
        console.log('继续执行');
    });

// 输出:
// 继续执行
// Uncaught Error: 异步错误
```

"果然!"你说,"try-catch 只能捕获同步错误,异步错误必须用 Promise 的 catch。"

你总结了规则:

```javascript
// ✅ 正确:用 Promise catch 捕获异步错误
function goodExample() {
    return asyncOperation()
        .catch(function(error) {
            console.log('捕获异步错误:', error);
        });
}

// ❌ 错误:try-catch 捕获不到异步错误
function badExample() {
    try {
        asyncOperation(); // 错误不会被 try-catch 捕获
    } catch (error) {
        console.log('这里捕获不到');
    }
}
```

---

## 修复生产环境的 Bug

下午六点,你开始修复生产环境的表单提交 bug。

你重写了代码,添加了完整的错误处理:

```javascript
function submitForm(formData) {
    // 显示加载状态
    const loadingIndicator = showLoading();

    return validateForm(formData)
        .then(function(validData) {
            return saveToDatabase(validData);
        })
        .catch(function(error) {
            // 数据库错误,尝试备份保存
            console.warn('主数据库保存失败,尝试备份');
            return saveToBackupDatabase(formData)
                .catch(function(backupError) {
                    // 备份也失败,记录详细错误
                    logError('表单保存失败', {
                        original: error,
                        backup: backupError,
                        formData: formData
                    });
                    throw new Error('数据保存失败,请稍后重试');
                });
        })
        .then(function(result) {
            // 发送确认邮件(失败不影响整体流程)
            return sendConfirmationEmail(result.userId)
                .catch(function(emailError) {
                    console.warn('确认邮件发送失败:', emailError);
                    // 不抛出错误,让流程继续
                });
        })
        .then(function() {
            showSuccessMessage('提交成功!');
        })
        .catch(function(error) {
            // 统一错误处理
            showErrorMessage(error.message);
            console.error('表单提交失败:', error);
        })
        .finally(function() {
            // 无论成功失败都清理 loading 状态
            hideLoading(loadingIndicator);
        });
}
```

你测试了各种失败场景:

1. **数据库主服务器失败** → 自动切换到备份 → 成功
2. **数据库完全失败** → 显示错误提示 → 数据被记录到日志
3. **邮件发送失败** → 记录警告但不影响用户 → 显示成功提示
4. **网络完全断开** → 显示友好的错误信息 → loading 被清理

"现在万无一失了,"你说,"每个错误都有对应的处理策略。"

---

## 你的错误处理笔记本

晚上八点,你整理了今天的收获。

你在笔记本上写下标题:"Promise 错误传播 —— 静默失败的噩梦"

### 核心洞察 #1: 错误会自动传播

你写道:

"Promise 链中,错误会自动向下传播,跳过所有 then,直到遇到 catch:

```javascript
doA()
    .then(doB) // 成功
    .then(doC) // 失败 ──┐
    .then(doD) // 跳过   │
    .then(doE) // 跳过   │
    .catch(handleError); // ◄─┘ 捕获
```

这是 Promise 的强大之处:不需要在每个 then 里判断错误,一个 catch 统一处理。

**危险**:如果没有 catch,错误会被浏览器吞掉,变成静默失败。"

### 核心洞察 #2: catch 可以恢复 Promise 链

"catch 不仅捕获错误,还能让 Promise 链恢复执行:

```javascript
doA()
    .then(doB) // 失败
    .catch(function(error) {
        console.warn('doB 失败,使用备选方案');
        return fallbackValue; // 返回备用值
    })
    .then(doC) // 继续执行,收到 fallbackValue
```

恢复规则:
- catch 返回普通值 → Promise 变为 fulfilled,继续执行 then
- catch 返回 Promise → 等待 Promise 完成,继续执行 then
- catch 抛出错误 → Promise 变为 rejected,需要另一个 catch"

### 核心洞察 #3: catch 的位置决定错误范围

"catch 只能捕获它之前的错误:

```javascript
// 场景 1: catch 在最后
doA().then(doB).then(doC).catch(handleAll); // 捕获所有错误

// 场景 2: catch 在中间
doA().then(doB).catch(handleB).then(doC); // 只捕获 doA/doB 的错误

// 场景 3: 多个 catch
doA()
    .catch(handleA) // 只捕获 doA
    .then(doB)
    .catch(handleB) // 只捕获 doB
    .then(doC)
    .catch(handleC); // 只捕获 doC
```

策略选择:
- 统一处理:catch 放在最后
- 分段恢复:catch 放在关键步骤后
- 精细控制:每个步骤都有独立 catch"

### 核心洞察 #4: finally 用于清理工作

"finally 无论成功失败都执行,用于清理资源:

```javascript
showLoading();

doAsync()
    .then(handleSuccess)
    .catch(handleError)
    .finally(function() {
        hideLoading(); // 一定会执行
    });
```

finally 特点:
- 无参数(不知道成功还是失败)
- 不改变 Promise 值(透传)
- 适合清理工作:关闭连接、隐藏 loading、释放资源"

### 核心洞察 #5: try-catch 不能捕获异步错误

"try-catch 只能捕获同步错误,异步错误必须用 Promise catch:

```javascript
// ❌ 错误:try-catch 捕获不到
try {
    asyncOperation(); // Promise 的错误不会被捕获
} catch (error) {
    // 这里捕获不到
}

// ✅ 正确:用 Promise catch
asyncOperation()
    .catch(function(error) {
        // 这里可以捕获
    });
```

规则:Promise 内部的错误只能用 Promise 的 catch 捕获。"

你合上笔记本,松了口气。

"明天要学习 Promise.all、Promise.race 这些批量操作,"你想,"今天终于理解了错误传播的机制——错误会自动向下传播,catch 可以恢复链条,但一定要记得加 catch,否则就是静默失败的噩梦。"

---

## 知识总结

**规则 1: Promise 的错误传播机制**

Promise 链中的错误会自动向下传播,跳过所有 then,直到遇到 catch:

```javascript
Promise.resolve(1)
    .then(function(value) {
        return value + 1; // 成功
    })
    .then(function(value) {
        throw new Error('步骤 2 出错'); // 抛出错误
    })
    .then(function(value) {
        console.log('步骤 3'); // 不会执行
    })
    .then(function(value) {
        console.log('步骤 4'); // 不会执行
    })
    .catch(function(error) {
        console.log('捕获错误:', error.message); // 捕获到错误
    });
```

传播路径:错误发生后,所有后续 then 被跳过,直接进入最近的 catch。

---

**规则 2: 必须添加 catch 避免静默失败**

Promise 链如果没有 catch,错误会被浏览器吞掉,导致静默失败:

```javascript
// ❌ 危险:没有 catch,错误被吞掉
function submitForm(data) {
    return saveData(data)
        .then(function() {
            showSuccess();
        });
    // 如果 saveData 失败,用户看不到任何提示!
}

// ✅ 正确:添加 catch 处理错误
function submitForm(data) {
    return saveData(data)
        .then(function() {
            showSuccess();
        })
        .catch(function(error) {
            showError(error.message);
            console.error('保存失败:', error);
        });
}
```

静默失败是最危险的 bug:用户以为操作成功,实际数据丢失。

---

**规则 3: catch 可以恢复 Promise 链**

catch 处理错误后,如果返回值或 Promise,链条会恢复执行:

```javascript
fetchData()
    .then(process)
    .catch(function(error) {
        console.warn('处理失败,使用缓存数据');
        return getCachedData(); // 返回备用数据
    })
    .then(function(data) {
        // 继续执行,data 可能是 process 的结果或缓存数据
        display(data);
    });
```

恢复规则:
- catch 返回普通值 → Promise 变为 fulfilled
- catch 返回 Promise → 等待 Promise 完成
- catch 抛出错误 → Promise 变为 rejected
- catch 不返回 → 返回 undefined,Promise 变为 fulfilled

---

**规则 4: catch 的位置决定捕获范围**

catch 只能捕获它之前的错误:

```javascript
// 场景 1: catch 在最后,捕获所有错误
doA()
    .then(doB)
    .then(doC)
    .catch(function(error) {
        // 捕获 doA, doB, doC 的任何错误
    });

// 场景 2: catch 在中间,只捕获部分错误
doA()
    .then(doB)
    .catch(function(error) {
        // 只捕获 doA, doB 的错误
        return fallback;
    })
    .then(doC) // doC 的错误不会被捕获!
    .catch(function(error) {
        // 捕获 doC 的错误
    });

// 场景 3: 每个操作都有独立 catch
doA()
    .catch(handleA)
    .then(doB)
    .catch(handleB)
    .then(doC)
    .catch(handleC);
```

位置策略:
- 统一处理:catch 放在最后
- 分段恢复:关键步骤后添加 catch
- 精细控制:每个步骤独立 catch

---

**规则 5: finally 用于清理工作**

finally 无论成功失败都执行,且不改变 Promise 的值:

```javascript
showLoading();

fetchData()
    .then(function(data) {
        processData(data);
    })
    .catch(function(error) {
        showError(error);
    })
    .finally(function() {
        hideLoading(); // 无论成功失败都隐藏 loading
    });
```

finally 特点:
- **无参数**:不知道是成功还是失败
- **透传值**:不改变 Promise 的值或错误
- **适合清理**:关闭连接、释放资源、隐藏 loading、移除监听器

finally 等价于:
```javascript
promise
    .then(
        function(value) {
            cleanup();
            return value;
        },
        function(error) {
            cleanup();
            throw error;
        }
    );
```

---

**规则 6: catch 里的错误继续传播**

catch 里的错误也会向下传播,需要另一个 catch 捕获:

```javascript
doA()
    .catch(function(error) {
        console.log('第一个 catch');
        throw new Error('catch 里的新错误'); // 抛出新错误
    })
    .then(function() {
        console.log('不会执行'); // 被跳过
    })
    .catch(function(error) {
        console.log('第二个 catch 捕获:', error.message);
    });
```

规则:
- catch 返回值 → 恢复链条
- catch 抛出错误 → 需要另一个 catch
- catch 返回 rejected Promise → 需要另一个 catch

---

**规则 7: try-catch 不能捕获异步错误**

try-catch 只能捕获同步错误,Promise 的异步错误必须用 catch:

```javascript
// ❌ 错误:try-catch 捕获不到 Promise 错误
try {
    asyncOperation()
        .then(function() {
            throw new Error('异步错误');
        });
} catch (error) {
    console.log('捕获不到'); // 不会执行
}

// ✅ 正确:用 Promise catch
asyncOperation()
    .then(function() {
        throw new Error('异步错误');
    })
    .catch(function(error) {
        console.log('捕获到:', error.message); // 会执行
    });

// ✅ then 内部的同步错误可以用 try-catch
.then(function() {
    try {
        JSON.parse(invalidJSON); // 同步错误
    } catch (error) {
        console.log('捕获到同步错误');
    }
})
```

规则:Promise 内部的错误只能用 Promise 的 catch 捕获,try-catch 无效。

---

**规则 8: 错误恢复的最佳实践**

实现自动重试、备选方案、降级策略:

```javascript
// 模式 1: 自动重试
function fetchWithRetry(url, retries = 3) {
    return fetch(url)
        .catch(function(error) {
            if (retries > 0) {
                console.log(`重试中,剩余 ${retries} 次`);
                return fetchWithRetry(url, retries - 1);
            }
            throw error; // 重试次数用完
        });
}

// 模式 2: 备选方案
function loadResource() {
    return loadFromCDN()
        .catch(function() {
            return loadFromBackup();
        })
        .catch(function() {
            return loadFromCache();
        });
}

// 模式 3: 部分失败继续
function processItems(items) {
    return Promise.all(
        items.map(function(item) {
            return processItem(item)
                .catch(function(error) {
                    console.warn('Item 处理失败:', item, error);
                    return null; // 返回 null 而非抛出错误
                });
        })
    );
}
```

策略选择:
- 关键操作:重试机制
- 非关键操作:降级或跳过
- 批量操作:捕获单项错误,继续处理其他项

---

**事故档案编号**: ASYNC-2024-1896
**影响范围**: Promise 错误传播, catch 方法, finally, 静默失败
**根本原因**: Promise 链缺少 catch,错误被浏览器吞掉,导致静默失败和数据丢失
**修复成本**: 低(添加 catch 处理错误)

这是 JavaScript 世界第 96 次被记录的 Promise 错误传播事故。Promise 链中的错误会自动向下传播,跳过所有 then,直到遇到 catch。没有 catch 的 Promise 链会导致静默失败——错误被浏览器吞掉,用户看不到任何提示。catch 不仅捕获错误,还能恢复 Promise 链:返回值或 Promise 让链条继续执行。catch 的位置决定捕获范围:最后统一处理、中间分段恢复、每步精细控制。finally 无论成功失败都执行,无参数,不改变 Promise 值,适合清理工作。catch 里的错误继续传播,需要另一个 catch。try-catch 只能捕获同步错误,Promise 的异步错误必须用 catch。错误恢复最佳实践:自动重试、备选方案、降级策略。理解错误传播和正确使用 catch 是避免静默失败的关键。

---
