# 🔧 Correcciones de Routing del Frontend

## 📋 Problemas Detectados

1. ✅ Admin general (`admin@psicoadmin.xyz`) está intentando login en tenant `bienestar`
2. ✅ Vercel desplegando en dominio incorrecto (`bienestar-psico-ml50pmcja...`)
3. ✅ Confusión sobre qué URL debe mostrar qué página

---

## 🎯 Arquitectura Correcta del Sistema

### 🌐 **Dominio Principal** (`psicoadmin.xyz`)

| URL | Página | Propósito |
|-----|--------|-----------|
| `https://psicoadmin.xyz/` | **LandingPage.jsx** | Formulario para registro de NUEVAS clínicas |
| `https://psicoadmin.xyz/login` | ❌ **NO DEBE EXISTIR** | El admin general usa Django Admin, NO el frontend |

### 🏥 **Subdominios de Clínicas** (`-app.psicoadmin.xyz`)

| URL | Página | Propósito |
|-----|--------|-----------|
| `https://bienestar-app.psicoadmin.xyz/` | **LandingPage.jsx** (con redirect) | Redirige automáticamente a `/login` |
| `https://bienestar-app.psicoadmin.xyz/login` | **LoginPage.jsx** | Login para admins/profesionales/pacientes |
| `https://bienestar-app.psicoadmin.xyz/register` | **RegisterPage.jsx** | Registro de nuevos pacientes |
| `https://bienestar-app.psicoadmin.xyz/dashboard` | **Dashboard** | Panel según rol (admin/pro/paciente) |

---

## 🔧 Cambios Necesarios en el Frontend

### 1️⃣ **Remover ruta de login del dominio principal**

**Archivo:** `src/main.jsx` o donde estén las rutas

```jsx
// ❌ ANTES (INCORRECTO):
<Route path="/login" element={<LoginPage />} />  // En psicoadmin.xyz

// ✅ DESPUÉS (CORRECTO):
// Solo la landing page en psicoadmin.xyz
<Route path="/" element={<LandingPage />} />
// NO debe haber ruta /login en psicoadmin.xyz
```

---

### 2️⃣ **Actualizar LandingPage.jsx para manejar ambos casos**

**Archivo:** `src/pages/LandingPage.jsx`

```jsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTenantFromHostname } from '../config/tenants';

function LandingPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const hostname = window.location.hostname;
    const currentTenant = getTenantFromHostname();

    // Si estamos en un subdominio de clínica (-app.psicoadmin.xyz)
    if (hostname.includes('-app.psicoadmin.xyz')) {
      // Verificar si la clínica existe
      checkTenantExists(currentTenant).then(exists => {
        if (exists) {
          // Redirigir automáticamente al login
          navigate('/login');
        } else {
          // Mostrar página de error "Clínica no encontrada"
          navigate('/404');
        }
      });
    }
    // Si estamos en el dominio principal (psicoadmin.xyz)
    // Mostrar el formulario de registro de nuevas clínicas (código actual)
  }, [navigate]);

  // ... resto del código actual ...
}
```

---

### 3️⃣ **Actualizar LoginPage.jsx para evitar confusión**

**Archivo:** `src/pages/LoginPage.jsx`

**Agregar validación al inicio:**

```jsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function LoginPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const hostname = window.location.hostname;

    // Si estamos en el dominio principal (sin -app)
    if (hostname === 'psicoadmin.xyz' || hostname === 'www.psicoadmin.xyz') {
      // El admin general NO usa este login, usa Django Admin
      alert('Para acceder como administrador del sistema, use: https://psico-admin.onrender.com/admin/');
      // Redirigir a la landing page
      navigate('/');
      return;
    }

    // Si llegamos aquí, estamos en un subdominio -app, continuar normal
  }, [navigate]);

  // ... resto del código actual ...
}
```

---

### 4️⃣ **Agregar página de información para admin general**

**Archivo nuevo:** `src/pages/AdminInfoPage.jsx`

```jsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function AdminInfoPage() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Administración del Sistema
          </h1>
          <p className="text-gray-600">
            Acceso para administradores globales
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">
            🔐 Panel de Administración
          </h2>
          <p className="text-blue-800 text-sm mb-4">
            Los administradores del sistema deben usar el panel de Django Admin:
          </p>
          <a
            href="https://psico-admin.onrender.com/admin/"
            target="_blank"
            rel="noopener noreferrer"
            className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg text-center transition-colors"
          >
            Ir a Django Admin →
          </a>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Credenciales:</h3>
          <div className="space-y-1 text-sm text-gray-700 font-mono">
            <p>📧 Email: admin@psicoadmin.xyz</p>
            <p>🔑 Password: admin123</p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link
            to="/"
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            ← Volver al inicio
          </Link>
        </div>
      </div>
    </div>
  );
}
```

**Agregar ruta en `main.jsx`:**

```jsx
<Route path="/admin-info" element={<AdminInfoPage />} />
```

---

### 5️⃣ **Actualizar configuración de Vercel**

**Problema actual:** Vercel está desplegando en `bienestar-psico-ml50pmcja-vazquescamila121...`

**Archivo:** `vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "env": {
    "NODE_ENV": "production"
  }
}
```

**Configurar dominios en Vercel Dashboard:**

1. Ve a tu proyecto en Vercel
2. Settings → Domains
3. **Agregar dominios:**
   - `psicoadmin.xyz` (principal)
   - `www.psicoadmin.xyz` (alias)
   - `bienestar-app.psicoadmin.xyz`
   - `mindcare-app.psicoadmin.xyz`
   - `*.psicoadmin.xyz` (wildcard para futuras clínicas)

4. **Remover dominios viejos:**
   - `bienestar-psico.vercel.app`
   - `bienestar-psico-ml50pmcja...`

---

### 6️⃣ **Actualizar el README del proyecto**

**Archivo:** `README.md` del frontend

Agregar sección:

```markdown
## 🌐 Arquitectura de URLs

### Dominio Principal
- `https://psicoadmin.xyz/` → Registro de nuevas clínicas
- `https://psicoadmin.xyz/admin-info` → Información para admins del sistema

### Admin del Sistema (Django)
- `https://psico-admin.onrender.com/admin/`
  - Email: admin@psicoadmin.xyz
  - Password: admin123

### Clínicas (Subdominios -app)
- `https://bienestar-app.psicoadmin.xyz/login` → Login
- `https://bienestar-app.psicoadmin.xyz/register` → Registro de pacientes
- `https://mindcare-app.psicoadmin.xyz/login` → Login

## 🔑 Credenciales de Prueba

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

- [ ] **1. Remover ruta `/login` del dominio principal**
- [ ] **2. Actualizar `LandingPage.jsx` para manejar redirect automático**
- [ ] **3. Agregar validación en `LoginPage.jsx`**
- [ ] **4. Crear `AdminInfoPage.jsx`**
- [ ] **5. Configurar dominios en Vercel**
- [ ] **6. Eliminar deployments viejos de Vercel**
- [ ] **7. Actualizar README**
- [ ] **8. Probar todas las URLs**

---

## 🧪 Testing

Después de implementar, probar:

1. ✅ `https://psicoadmin.xyz/` → Muestra formulario de registro de clínicas
2. ✅ `https://psicoadmin.xyz/login` → Redirige a `/admin-info` o `/`
3. ✅ `https://bienestar-app.psicoadmin.xyz/` → Redirige a `/login`
4. ✅ `https://bienestar-app.psicoadmin.xyz/login` → Muestra formulario de login
5. ✅ Login con `admin@bienestar.com` / `admin123` → Funciona
6. ✅ Login con `admin@psicoadmin.xyz` en bienestar-app → Muestra error claro

---

## 📞 Soporte

Si tienes dudas sobre la implementación, revisa:
- Backend: `apps/authentication/views.py` (línea 57)
- Logs de Render: https://dashboard.render.com
- Arquitectura: `DEPLOY_RENDER.md`
