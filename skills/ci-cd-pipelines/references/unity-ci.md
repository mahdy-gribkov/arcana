# Game engine CI (Unity)

Loaded from SKILL.md. Use this for Unity build and test pipelines.

Uses [game-ci](https://game.ci/) actions. Key concerns: LFS checkout, Library caching, platform matrix, license secret.

```yaml
# .github/workflows/unity.yml
name: Unity Build
on:
  push:
    branches: [main, develop]
env:
  UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { lfs: true }
      - uses: actions/cache@v4
        with:
          path: Library
          key: Library-${{ hashFiles('Assets/**', 'Packages/**', 'ProjectSettings/**') }}
          restore-keys: Library-
      - uses: game-ci/unity-test-runner@v4
        with: { testMode: all, artifactsPath: test-results }
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: test-results, path: test-results }

  build:
    needs: test
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        targetPlatform: [StandaloneWindows64, StandaloneLinux64, WebGL, Android]
    steps:
      - uses: actions/checkout@v4
        with: { lfs: true }
      - uses: actions/cache@v4
        with:
          path: Library
          key: Library-${{ matrix.targetPlatform }}-${{ hashFiles('Assets/**') }}
          restore-keys: Library-${{ matrix.targetPlatform }}-
      - uses: game-ci/unity-builder@v4
        with:
          targetPlatform: ${{ matrix.targetPlatform }}
          versioning: Semantic
          buildMethod: BuildScript.PerformBuild
      - uses: actions/upload-artifact@v4
        with:
          name: Build-${{ matrix.targetPlatform }}
          path: build/${{ matrix.targetPlatform }}
          retention-days: 14
```

### BuildScript.cs
```csharp
// Assets/Editor/BuildScript.cs
using UnityEditor;
using UnityEditor.Build.Reporting;

public class BuildScript
{
    public static void PerformBuild()
    {
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = new[] { "Assets/Scenes/Main.unity" },
            locationPathName = "build/Game.exe",
            target = BuildTarget.StandaloneWindows64,
            options = BuildOptions.None
        });
        if (report.summary.result != BuildResult.Succeeded)
            EditorApplication.Exit(1);
    }
}
```

### PlayMode Test
```csharp
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using System.Collections;

public class PlayerMovementTests
{
    private GameObject _player;

    [UnitySetUp]
    public IEnumerator SetUp()
    {
        _player = Object.Instantiate(Resources.Load<GameObject>("Prefabs/Player"));
        yield return null;
    }

    [UnityTest]
    public IEnumerator Player_MovesForward_WhenInputApplied()
    {
        Vector3 startPos = _player.transform.position;
        _player.GetComponent<PlayerController>().SetInput(Vector2.up);
        yield return new WaitForSeconds(0.5f);
        Assert.Greater(_player.transform.position.z, startPos.z);
    }

    [UnityTearDown]
    public IEnumerator TearDown() { Object.Destroy(_player); yield return null; }
}
```

Unity CI rules:
- Always `lfs: true`. Unity projects use Git LFS for assets.
- Cache `Library/` with per-platform keys. Regeneration takes 5-15 min.
- `testMode: all` runs EditMode + PlayMode. Split if needed.
- Build times: WebGL 10-20 min, Windows 5-10 min, Android 15-25 min.
