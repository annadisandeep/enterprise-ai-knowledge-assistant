import "@testing-library/jest-dom";

// jsdom lacks scrollTo; stub it so components that auto-scroll don't crash.
if (!window.HTMLElement.prototype.scrollTo) {
  window.HTMLElement.prototype.scrollTo = () => {};
}
