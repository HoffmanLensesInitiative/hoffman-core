# Hoffman Browser - Setup Guide

The node-llama-cpp + Electron combination requires a specific setup.
Follow these steps exactly.

## Step 1: Delete node_modules and reinstall

In your hoffman-browser folder:

```
rmdir /s /q node_modules
del package-lock.json
npm install
```

## Step 2: Download node-llama-cpp binaries for Electron

This is the critical step. node-llama-cpp needs Electron-specific
binaries, not the default Node.js ones:

```
npx --no node-llama-cpp download --electron
```

Wait for this to complete. It downloads pre-built binaries
compatible with Electron's version of Node.js.

## Step 3: Start the app

```
npm start
```

## Why this matters

node-llama-cpp ships different native binaries for:
- Regular Node.js
- Electron (different V8/Node version bundled)

Running `npx node-llama-cpp download --electron` downloads
the correct binaries for your specific Electron version.
Without this step, it tries to use Node.js binaries inside
Electron which causes the "Unexpected token 'with'" error.

