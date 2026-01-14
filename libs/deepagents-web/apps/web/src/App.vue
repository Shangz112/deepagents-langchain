<template>
  <AppShell>
    <router-view />
    <template #right>
      <RightPanel />
    </template>
  </AppShell>
</template>

<script setup lang="ts">
import AppShell from './layouts/AppShell.vue'
import RightPanel from './components/RightPanel.vue'
</script>

<style>
/* Global Overrides */
html, body {
  height: 100%;
  overflow: hidden;
  background-color: #e6edf5;
}
#app {
  height: 100%;
}
</style>