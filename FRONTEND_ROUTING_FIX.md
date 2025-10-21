# 🔧 Estado Actual y Cambios Pendientes del Frontend

## ✅ CAMBIOS YA IMPLEMENTADOS (Commit: af9d875)

### 1️⃣ **LandingPage.jsx - ✅ FUNCIONANDO**
- Detecta si está en dominio raíz (`psicoadmin.xyz`)
- Muestra formulario de registro de clínicas en dominio raíz
- Redirige a `/login` solo en subdominios `-app`

### 2️⃣ **tenants.js - ✅ FUNCIONANDO**
- `getApiBaseURL()` remueve `-app` del hostname
- Frontend en `bienestar-app` apunta a backend `bienestar`

### 3️⃣ **Routing - ✅ FUNCIONANDO**
- `/` → LandingPage (registro de clínicas en raíz, redirect en subdominios)
- `/login` → LoginPage (funciona en ambos dominios)
- `/register` → RegisterPage (solo subdominios)

---

## ⚠️ PROBLEMA ACTUAL

### 🐛 **Error 400 en Login**

**Logs del backend:**
```
INFO    request.data: {'email': 'admin@psicoadmin.xyz', 'password': 'admin123'}
ERROR   Credenciales inválidas o usuario inactivo
```

**Causa:** El frontend está enviando login del admin general (`admin@psicoadmin.xyz`) al backend del tenant `bienestar` en lugar del backend público.

**URL incorrecta:** 
```
❌ https://bienestar.psicoadmin.xyz/api/auth/login/
```

**URL correcta:**
```
✅ https://psico-admin.onrender.com/api/auth/login/
```

---

## 🔧 CAMBIOS PENDIENTES

### ⚠️ **SOLO FALTA ESTO:** LoginPage.jsx

---

## 🔧 CAMBIOS PENDIENTES

### ⚠️ **SOLO FALTA ESTO:** Modificar LoginPage.jsx

**El problema:** LoginPage actual no diferencia entre admin general y usuarios de clínica.

**Solución:** Agregar lógica para detectar tipo de usuario y usar el backend correcto.

**Archivo:** `src/pages/LoginPage.jsx` (o donde esté tu componente de login)

**Cambios necesarios:**

```jsx
// DENTRO del handleLogin, ANTES de hacer el fetch:

const handleLogin = async (e) => {
  e.preventDefault();

  const hostname = window.location.hostname;
  const isRootDomain = hostname === 'psicoadmin.xyz' || hostname === 'www.psicoadmin.xyz';
  const isClinicDomain = hostname.includes('-app.psicoadmin.xyz');

  // 🔍 Detectar tipo de usuario por el email
  const isGlobalAdmin = email === 'admin@psicoadmin.xyz';

  // 🚫 CASO 1: Admin general intentando login en dominio de clínica
  if (isGlobalAdmin && isClinicDomain) {
    alert('⚠️ Usuario admin global detectado.\n\nDebe iniciar sesión en: https://psicoadmin.xyz/login');
    window.location.href = 'https://psicoadmin.xyz/login';
    return;
  }

  // 🚫 CASO 2: Usuario de clínica intentando login en dominio raíz
  if (!isGlobalAdmin && isRootDomain) {
    // Extraer nombre de la clínica del email
    const emailDomain = email.split('@')[1]; // ej: bienestar.com
    const clinicName = emailDomain.split('.')[0]; // ej: bienestar
    
    alert(`⚠️ Usuario de clínica detectado.\n\nDebe iniciar sesión en: https://${clinicName}-app.psicoadmin.xyz/login`);
    window.location.href = `https://${clinicName}-app.psicoadmin.xyz/login`;
    return;
  }

  // ✅ CASO 3: Usuario correcto en dominio correcto
  try {
    // 🎯 ESTA ES LA PARTE CLAVE:
    const apiUrl = isRootDomain && isGlobalAdmin
      ? 'https://psico-admin.onrender.com/api/auth/login/'  // Backend público
      : getApiBaseURL() + '/auth/login/';  // Backend del tenant

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (response.ok) {
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate('/dashboard');
    } else {
      alert('Credenciales inválidas');
    }
  } catch (error) {
    console.error('Error en el login:', error);
    alert('Error de conexión');
  }
};
```

---

## 📝 RESUMEN DE LO QUE FALTA

### ✅ Ya funciona:
- ✅ LandingPage detecta dominio correctamente
- ✅ Routing configurado
- ✅ getApiBaseURL() funciona para subdominios

### ⚠️ Falta implementar:
- ❌ **LoginPage.jsx:** Detectar admin general y usar backend público
- ❌ **LoginPage.jsx:** Validar que usuario coincida con dominio
- ❌ **LoginPage.jsx:** Mostrar alertas y redirigir si hay error

---

## 🧪 Testing después del cambio

Una vez implementado, probar:

1. ✅ Login en `psicoadmin.xyz/login` con `admin@psicoadmin.xyz` → Debe funcionar
2. ✅ Login en `psicoadmin.xyz/login` con `admin@bienestar.com` → Debe redirigir a bienestar-app
3. ✅ Login en `bienestar-app.../login` con `admin@psicoadmin.xyz` → Debe redirigir a psicoadmin.xyz
4. ✅ Login en `bienestar-app.../login` con `admin@bienestar.com` → Debe funcionar

---

## 📋 Código completo sugerido para LoginPage.jsx

```jsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTenantFromHostname } from '../config/tenants';

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();

    const hostname = window.location.hostname;
    const isMainDomain = hostname === 'psicoadmin.xyz' || hostname === 'www.psicoadmin.xyz';
    const isClinicDomain = hostname.includes('-app.psicoadmin.xyz');

    // Verificar si es el admin general
    const isGlobalAdmin = email === 'admin@psicoadmin.xyz';

    // CASO 1: Admin general intentando login en dominio de clínica
    if (isGlobalAdmin && isClinicDomain) {
      alert('⚠️ Usuario admin global detectado.\n\nDebe iniciar sesión en: https://psicoadmin.xyz/login');
      window.location.href = 'https://psicoadmin.xyz/login';
      return;
    }

    // CASO 2: Admin de clínica intentando login en dominio principal
    if (!isGlobalAdmin && isMainDomain) {
      // Extraer el dominio de la clínica del email
      const emailDomain = email.split('@')[1]; // ej: bienestar.com
      const clinicName = emailDomain.split('.')[0]; // ej: bienestar
      
      alert(`⚠️ Usuario de clínica detectado.\n\nDebe iniciar sesión en: https://${clinicName}-app.psicoadmin.xyz/login`);
      window.location.href = `https://${clinicName}-app.psicoadmin.xyz/login`;
      return;
    }

    // CASO 3: Login correcto - continuar con la petición
    try {
      const apiUrl = isMainDomain 
        ? 'https://psico-admin.onrender.com/api/auth/login/'  // Backend público
        : getApiBaseURL() + '/auth/login/';  // Backend del tenant

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // Guardar token y redirigir al dashboard
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        navigate('/dashboard');
      } else {
        alert('Credenciales inválidas: ' + (data.non_field_errors?.[0] || 'Error desconocido'));
      }
    } catch (error) {
      console.error('Error en el login:', error);
      alert('Error de conexión. Intente nuevamente.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6 text-center">
          Iniciar Sesión
        </h1>

        <form onSubmit={handleLogin}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="tu@email.com"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-colors"
          >
            Iniciar Sesión
          </button>
        </form>

        {/* Info adicional */}
        <div className="mt-4 text-sm text-gray-600 text-center">
          <p>¿No tienes cuenta? <a href="/register" className="text-blue-600 hover:underline">Regístrate</a></p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
```

---

## � Credenciales de Prueba

### Bienestar
- Admin: `admin@bienestar.com` / `admin123`
- Profesional: `dra.martinez@bienestar.com` / `demo123`
- Paciente: `juan.perez@example.com` / `demo123`

### Mindcare
- Admin: `admin@mindcare.com` / `admin123`
- Profesional: `dra.torres@mindcare.com` / `demo123`
- Paciente: `carlos.ruiz@example.com` / `demo123`
```

---

## ✅ Checklist de Implementación

- [ ] **1. Configurar routing con /login en ambos dominios**
- [ ] **2. Actualizar `LoginPage.jsx` con detección inteligente de usuario**
- [ ] **3. Actualizar `LandingPage.jsx` para redirect automático en subdominios**
- [ ] **4. Crear `GlobalAdminDashboard.jsx` (opcional)**
- [ ] **5. Configurar dominios en Vercel**
- [ ] **6. Eliminar deployments viejos de Vercel**
- [ ] **7. Actualizar README**
- [ ] **8. Probar todas las URLs**

---

## 🧪 Testing

Después de implementar, probar:

1. ✅ `https://psicoadmin.xyz/` → Muestra formulario de registro de clínicas
2. ✅ `https://psicoadmin.xyz/login` → Login del admin general (admin@psicoadmin.xyz)
3. ✅ `https://psicoadmin.xyz/login` con usuario de clínica → Redirige a `bienestar-app.../login`
4. ✅ `https://bienestar-app.psicoadmin.xyz/` → Redirige a `/login`
5. ✅ `https://bienestar-app.psicoadmin.xyz/login` → Muestra formulario de login
6. ✅ `https://bienestar-app.psicoadmin.xyz/login` con admin general → Redirige a `psicoadmin.xyz/login`
7. ✅ Login con `admin@bienestar.com` / `admin123` en bienestar-app → Funciona
8. ✅ Login con `admin@psicoadmin.xyz` / `admin123` en psicoadmin.xyz → Funciona

---

## 📞 Soporte

Si tienes dudas sobre la implementación, revisa:
- Backend: `apps/authentication/views.py` (línea 57)
- Logs de Render: https://dashboard.render.com
- Arquitectura: `DEPLOY_RENDER.md`
