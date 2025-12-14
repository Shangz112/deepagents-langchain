import { createRouter, createWebHistory } from 'vue-router'
import ChatView from './views/ChatView.vue'
import PlanGraph from './views/PlanGraph.vue'
import ConfigPanel from './views/ConfigPanel.vue'
import PromptStudio from './views/PromptStudio.vue'
import KnowledgeBase from './views/KnowledgeBase.vue'
import SkillsView from './views/SkillsView.vue'
export default createRouter({ history: createWebHistory(), routes: [ { path: '/', component: ChatView }, { path: '/plan', component: PlanGraph }, { path: '/config', component: ConfigPanel }, { path: '/prompts', component: PromptStudio }, { path: '/kb', component: KnowledgeBase }, { path: '/skills', component: SkillsView } ] })