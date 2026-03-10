<template>
  <router-view></router-view>
</template>

<script setup lang="ts">
// El punto de entrada principal simplemente carga el Vue Router
</script>

<style>
/* Reset base */
html, body {
  margin: 0;
  padding: 0;
  font-family: var(--p-font-family);
  background-color: var(--p-content-background);
  color: var(--p-text-color);
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>