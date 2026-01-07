#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import sys

def fix_colon_spacing(content):
    """修复时间标记中冒号后缺少的空格"""
    lines = content.split('\n')
    result = []
    in_code_block = False
    
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            continue
        
        if in_code_block:
            result.append(line)
            continue
        
        # 保护行内代码
        inline_code_parts = []
        def save_inline_code(match):
            inline_code_parts.append(match.group(0))
            return f'__INLINE_CODE_{len(inline_code_parts)-1}__'
        
        line = re.sub(r'`[^`]+`', save_inline_code, line)
        
        # 修复 "分钟):" 这样的模式,在冒号后添加空格
        line = re.sub(r'\):([0-9])', r'): \1', line)
        
        # 恢复行内代码
        for i, code in enumerate(inline_code_parts):
            line = line.replace(f'__INLINE_CODE_{i}__', code)
        
        result.append(line)
    
    return '\n'.join(result)

if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixed_content = fix_colon_spacing(content)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed colon spacing in {filename}")
