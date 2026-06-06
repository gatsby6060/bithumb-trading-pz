const fs = require('fs');
const readline = require('readline');
const { execSync } = require('child_process');

async function main() {
  let inputData = '';
  try {
    inputData = fs.readFileSync(0, 'utf-8');
  } catch (e) {
    console.log(JSON.stringify({}));
    return;
  }

  let data;
  try {
    data = JSON.parse(inputData);
  } catch (e) {
    console.log(JSON.stringify({}));
    return;
  }

  const stepIndex = data.stepIndex !== undefined ? data.stepIndex : data.stepIdx;
  const transcriptPath = data.transcriptPath;

  if (!transcriptPath || stepIndex === undefined) {
    console.log(JSON.stringify({}));
    return;
  }

  let targetFile = '';
  try {
    const fileStream = fs.createReadStream(transcriptPath);
    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity
    });

    for await (const line of rl) {
      if (!line) continue;
      const logEntry = JSON.parse(line);
      if (logEntry.step_index === stepIndex && logEntry.tool_calls) {
        for (const tc of logEntry.tool_calls) {
          let args = tc.args || {};
          if (typeof args === 'string') {
            try {
              args = JSON.parse(args);
            } catch (e) {}
          }
          const candidate = args.TargetFile || args.targetFile;
          if (candidate) {
            targetFile = candidate;
            if (typeof targetFile === 'string') {
              targetFile = targetFile.replace(/^["']|["']$/g, '');
            }
          }
        }
      }
    }
  } catch (e) {
    // Fail silently on read error
  }

  if (!targetFile || !fs.existsSync(targetFile)) {
    console.log(JSON.stringify({}));
    return;
  }

  try {
    if (targetFile.endsWith('.js')) {
      // Run prettier formatting on JavaScript files
      execSync(`npx prettier --write "${targetFile}"`, { stdio: 'ignore' });
    } else if (targetFile.endsWith('.py')) {
      // Run black formatting on Python files
      execSync(`python -m black "${targetFile}"`, { stdio: 'ignore' });
    }
  } catch (err) {
    // Fail silently on execution errors to not block agent operation
  }

  console.log(JSON.stringify({}));
}

main();
