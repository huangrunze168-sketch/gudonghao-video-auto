# first-draft-k50ekinv

## 保存工作并完全退出剪映后，登记到本机首页

```powershell
C:\Python314\python.exe C:\Users\Administrator\Documents\剪映\skills\yichen-jianying-edit\scripts\headless_draft.py publish --build C:\Users\Administrator\Documents\剪映\work\onboarding-tests\case-wh14_a1c\work\first-draft-k50ekinv\build --audit C:\Users\Administrator\Documents\剪映\work\onboarding-tests\case-wh14_a1c\work\first-draft-k50ekinv\publish-audit
```

## 打开播放、保存退出、冷重开检查，再次退出后回读

```powershell
C:\Python314\python.exe C:\Users\Administrator\Documents\剪映\skills\yichen-jianying-edit\scripts\headless_draft.py verify --build C:\Users\Administrator\Documents\剪映\work\onboarding-tests\case-wh14_a1c\work\first-draft-k50ekinv\build --report C:\Users\Administrator\Documents\剪映\work\onboarding-tests\case-wh14_a1c\work\first-draft-k50ekinv\after-native-save.json
```

## 可选：导出最初构建的快照，不包含后来手工修改（Windows 目前不可用）

```powershell
C:\Python314\python.exe C:\Users\Administrator\Documents\剪映\skills\yichen-jianying-edit\scripts\headless_draft.py export --build C:\Users\Administrator\Documents\剪映\work\onboarding-tests\case-wh14_a1c\work\first-draft-k50ekinv\build --out C:\Users\Administrator\Documents\剪映\work\onboarding-tests\case-wh14_a1c\work\first-draft-k50ekinv\export
```
