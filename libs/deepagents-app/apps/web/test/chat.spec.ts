import { mount } from '@vue/test-utils'
import ChatView from '../src/views/ChatView.vue'
test('renders input', () => { const w = mount(ChatView); expect(w.find('input').exists()).toBe(true) })