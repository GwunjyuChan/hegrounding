/* Resolve workspace resources against the server-configured HTML base path. */
function workspaceURL(path) {
  return new URL(path.replace(/^\//, ''), document.baseURI).href;
}
