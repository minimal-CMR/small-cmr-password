import axios from 'axios';

const api = axios.create({ baseURL: '' });

const token = localStorage.getItem('token');
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

window.addEventListener('storage', e => {
  if (e.key === 'token') {
    if (e.newValue) {
      api.defaults.headers.common['Authorization'] = `Bearer ${e.newValue}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  }
});

export default api;
