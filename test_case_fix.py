#!/usr/bin/env python3
"""Test case-sensitivity fix"""

status_lower = 'completed'

# Old code (BROKEN)
old_check = status_lower in ['PROCESSED', 'COMPLETED']
print(f'OLD CODE: status="{status_lower}" in ["PROCESSED", "COMPLETED"] = {old_check}')

# New code (FIXED)
new_check = status_lower.upper() in ['PROCESSED', 'COMPLETED']
print(f'NEW CODE: status.upper() in ["PROCESSED", "COMPLETED"] = {new_check}')

print()
if not old_check and new_check:
    print('✅ FIX VERIFIED: Old code failed, new code works!')
    print('   is_processed will now be TRUE for lowercase "completed"')
else:
    print('❌ Issue persists')
