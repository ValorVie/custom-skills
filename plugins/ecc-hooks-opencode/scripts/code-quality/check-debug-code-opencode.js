#!/usr/bin/env node

const { checkAllFiles } = require("./lib/check-debug-code");

const warnings = checkAllFiles();
warnings.forEach((warning) => console.error(warning));
