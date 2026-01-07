《第75次记录：装饰器模式 —— 函数的优雅包装》

---

## 周末实验

周六上午十点，你坐在家里的工作台前，窗外阳光正好。这周工作中遇到一个有趣的问题：项目里有20多个API函数，每个都需要添加日志、错误处理、重试逻辑。

"如果一个个改，要改20多处，太麻烦了。"你一边喝咖啡一边想，"Python有装饰器`@decorator`，JavaScript能不能也做类似的东西？"

你打开编辑器，决定利用周末时间探索一下。这不是工作任务，纯粹是技术好奇心驱使的小实验。

首先看看现状：

```javascript
// 现有的API函数（重复代码很多）
async function getUserData(userId) {
    console.log(`[API] 调用 getUserData, userId: ${userId}`);
    try {
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        console.log(`[API] getUserData 成功`);
        return data;
    } catch (error) {
        console.error(`[API] getUserData 失败:`, error);
        throw error;
    }
}

async function getOrderData(orderId) {
    console.log(`[API] 调用 getOrderData, orderId: ${orderId}`);
    try {
        const response = await fetch(`/api/orders/${orderId}`);
        const data = await response.json();
        console.log(`[API] getOrderData 成功`);
        return data;
    } catch (error) {
        console.error(`[API] getOrderData 失败:`, error);
        throw error;
    }
}
```

"日志和错误处理的代码几乎一模一样，这明显违反DRY原则。"你皱起眉头。

周末的时光很悠闲，你可以慢慢实验。"试试用高阶函数把这些通用逻辑抽出来。"

---

## 构建装饰器

上午十一点，你开始动手实现第一个装饰器：

```javascript
// 日志装饰器
function withLogging(fn) {
    return async function(...args) {
        console.log(`[LOG] 调用 ${fn.name}, 参数:`, args);
        const result = await fn(...args);
        console.log(`[LOG] ${fn.name} 返回:`, result);
        return result;
    };
}

// 使用装饰器
const getUserData = withLogging(async function getUserData(userId) {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
});

// 调用
await getUserData(123);
// [LOG] 调用 getUserData, 参数: [123]
// [LOG] getUserData 返回: {id: 123, name: "Alice"}
```

"成功了！"你兴奋地看着输出。"装饰器就是一个接收函数、返回新函数的高阶函数。"

接着你实现错误处理装饰器：

```javascript
// 错误处理装饰器
function withErrorHandler(fn) {
    return async function(...args) {
        try {
            return await fn(...args);
        } catch (error) {
            console.error(`[ERROR] ${fn.name} 失败:`, error.message);
            throw error;
        }
    };
}
```

然后是重试装饰器：

```javascript
// 重试装饰器
function withRetry(maxRetries = 3) {
    return function(fn) {
        return async function(...args) {
            for (let i = 0; i < maxRetries; i++) {
                try {
                    return await fn(...args);
                } catch (error) {
                    if (i === maxRetries - 1) throw error;
                    console.log(`[RETRY] ${fn.name} 重试 ${i + 1}/${maxRetries}`);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
        };
    };
}
```

"现在可以组合使用了！"你写下测试代码：

```javascript
// 组合多个装饰器
let fetchUser = async function fetchUser(userId) {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
};

fetchUser = withLogging(fetchUser);
fetchUser = withErrorHandler(fetchUser);
fetchUser = withRetry(3)(fetchUser);

// 调用时自动应用所有装饰器
await fetchUser(123);
```

---

## 组合应用

下午两点，你优化了装饰器的组合方式：

```javascript
// 通用装饰器组合函数
function compose(...decorators) {
    return function(fn) {
        return decorators.reduceRight((wrapped, decorator) => {
            return decorator(wrapped);
        }, fn);
    };
}

// 优雅的使用方式
const fetchUser = compose(
    withLogging,
    withErrorHandler,
    withRetry(3)
)(async function fetchUser(userId) {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
});
```

你又实现了几个实用装饰器：

```javascript
// 性能监控装饰器
function withPerformance(fn) {
    return async function(...args) {
        const start = performance.now();
        const result = await fn(...args);
        const duration = performance.now() - start;
        console.log(`[PERF] ${fn.name} 耗时: ${duration.toFixed(2)}ms`);
        return result;
    };
}

// 缓存装饰器
function withCache(fn) {
    const cache = new Map();
    return function(...args) {
        const key = JSON.stringify(args);
        if (cache.has(key)) {
            console.log(`[CACHE] ${fn.name} 命中缓存`);
            return cache.get(key);
        }
        const result = fn(...args);
        cache.set(key, result);
        return result;
    };
}
```

下午四点，你测试了完整的装饰器链：

```javascript
const api = compose(
    withLogging,
    withPerformance,
    withErrorHandler,
    withRetry(3),
    withCache
)(async function fetchData(id) {
    const response = await fetch(`/api/data/${id}`);
    return response.json();
});

await api(123);
// [LOG] 调用 fetchData, 参数: [123]
// [PERF] fetchData 耗时: 234.56ms
// [LOG] fetchData 返回: {...}

await api(123); // 第二次调用
// [CACHE] fetchData 命中缓存
```

"完美！一个函数定义，多个装饰器增强。"你满意地伸了个懒腰。

---

## 装饰器模式

晚上八点，你整理了装饰器模式的核心知识：

**规则 1: 装饰器基础**

装饰器是接收函数并返回增强函数的高阶函数：

```javascript
function decorator(fn) {
    return function(...args) {
        // 前置逻辑
        const result = fn(...args);
        // 后置逻辑
        return result;
    };
}
```

---

**规则 2: 装饰器工厂**

需要配置的装饰器使用工厂模式：

```javascript
function withTimeout(ms) {
    return function(fn) {
        return async function(...args) {
            return Promise.race([
                fn(...args),
                new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('超时')), ms)
                )
            ]);
        };
    };
}

const api = withTimeout(5000)(fetchData);
```

---

**规则 3: 保留函数元信息**

装饰后保留原函数的name和其他属性：

```javascript
function preserveMetadata(wrapper, original) {
    Object.defineProperty(wrapper, 'name', {
        value: original.name,
        configurable: true
    });
    wrapper.length = original.length;
    return wrapper;
}
```

---

**规则 4: 装饰器组合**

多个装饰器从右到左应用：

```javascript
function compose(...decorators) {
    return fn => decorators.reduceRight((acc, dec) => dec(acc), fn);
}

// 等价于: dec1(dec2(dec3(fn)))
const enhanced = compose(dec1, dec2, dec3)(fn);
```

---

**规则 5: 常见装饰器模式**

```javascript
// 节流装饰器
function throttle(ms) {
    return function(fn) {
        let lastRun = 0;
        return function(...args) {
            const now = Date.now();
            if (now - lastRun >= ms) {
                lastRun = now;
                return fn(...args);
            }
        };
    };
}

// 防抖装饰器
function debounce(ms) {
    return function(fn) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn(...args), ms);
        };
    };
}
```

---

**规则 6: 实践建议**

- 装饰器应该是纯函数，无副作用
- 保持单一职责，每个装饰器只做一件事
- 注意装饰器的顺序，会影响最终行为
- 避免过度装饰，保持代码可读性

---

周日上午，你把这套装饰器系统应用到项目中，20多个API函数的重复代码全部消除。代码量减少了40%，可维护性大幅提升。

"装饰器模式真是优雅，"你感慨道，"函数式编程的魅力就在于此——用组合代替重复，用抽象简化复杂。"

---

**事故档案编号**: FUNC-2024-1875
**影响范围**: 装饰器模式,高阶函数,函数组合,代码复用
**根本原因**: 重复的横切关注点(日志/错误/重试)未抽象,违反DRY原则
**修复成本**: 低(实现装饰器),代码量减少40%,可维护性显著提升

这是JavaScript世界第75次被记录的装饰器模式实践。装饰器是接收函数并返回增强函数的高阶函数,用于在不修改原函数的情况下添加功能。核心优势:分离关注点、代码复用、组合灵活。通过compose函数可优雅组合多个装饰器,从右到左应用。常见应用:日志、错误处理、性能监控、缓存、重试、节流防抖。装饰器应保持纯函数特性、单一职责,并注意组合顺序。这是函数式编程的精髓——用组合代替继承,用抽象消除重复。

---
