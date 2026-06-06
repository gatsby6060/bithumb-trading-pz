const fs = require('fs');

function main() {
  let inputData = '';
  try {
    inputData = fs.readFileSync(0, 'utf-8');
  } catch (e) {
    console.log(JSON.stringify({ decision: "allow" }));
    return;
  }

  let data;
  try {
    data = JSON.parse(inputData);
  } catch (e) {
    console.log(JSON.stringify({ decision: "allow" }));
    return;
  }

  // Supporting multiple potential schema structures (camelCase and snake_case)
  const toolCall = data.toolCall || {};
  const args = data.arguments || data.args || toolCall.args || toolCall.arguments || {};
  const commandLine = args.CommandLine || args.commandLine || "";

  if (!commandLine) {
    console.log(JSON.stringify({ decision: "allow" }));
    return;
  }

  const lowerCmd = commandLine.toLowerCase();

  // Patterns matching env dumping or .env file viewing
  const forbiddenPatterns = [
    /\bprintenv\b/,
    /\benv\b/,
    /\bdir\s+env\b/,
    /\bget-childitem\s+env\b/,
    /\bcat\s+\.env\b/,
    /\btype\s+\.env\b/,
    /\bget-content\s+\.env\b/
  ];

  const matched = forbiddenPatterns.some(pattern => pattern.test(lowerCmd));

  if (matched) {
    console.log(JSON.stringify({
      decision: "deny",
      reason: "API Key safety violation: Dumping environment variables or reading .env directly is forbidden."
    }));
  } else {
    console.log(JSON.stringify({
      decision: "allow"
    }));
  }
}

main();
