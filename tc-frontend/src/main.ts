import { mount } from 'svelte'
import './styles/app.css'
import './styles/modal-fix.css'
import './modules'
import App from './App.svelte'

const app = mount(App, {
  target: document.getElementById('app')!,
})

export default app
