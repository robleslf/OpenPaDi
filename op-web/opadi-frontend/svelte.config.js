import adapter from '@sveltejs/adapter-static';

const config = {
  kit: {
    adapter: adapter({
      fallback: 'index.html',  // Configura el fallback para manejar rutas dinámicas
    }),
    paths: {
      base: process.env.NODE_ENV === 'production' ? '/opadi' : '',  // Esto es útil si tu proyecto está en una subcarpeta
    },
  },
};

export default config;
