import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, ArrowRight, Eye, EyeOff } from 'lucide-react';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    React.useEffect(() => {
        document.title = 'Competence CRM Login';
    }, []);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();

            if (res.ok) {
                sessionStorage.setItem('token', data.access_token);
                sessionStorage.setItem('currentUser', JSON.stringify(data.user));

                if (role === 'employee') {
                    // Redirect to Legacy Dashboard on Port 3000 with token AND user
                    const userStr = encodeURIComponent(JSON.stringify(data.user));
                    window.location.href = `/employee_dashboard_page/index.html?token=${data.access_token}&user=${userStr}`;
                } else {
                    // Manager/Admin stays in React App
                    navigate('/');
                }
            } else {
                alert(data.detail || 'Login failed');
            }
        } catch (error) {
            console.error(error);
            alert('Connection failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 relative font-sans text-slate-800">
            {/* Background Grid Pattern */}
            <div className="absolute inset-0 z-0 opacity-10 pointer-events-none"
                style={{
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Cpath d='M0 0h40v40H0V0zm1 1h38v38H1V1z' fill='%2394a3b8' fill-opacity='1' fill-rule='evenodd'/%3E%3C/svg%3E")`,
                    backgroundSize: '20px 20px'
                }}
            />
            {/* Gradient Overlay */}
            <div className="absolute inset-0 z-0 bg-gradient-to-br from-slate-50 to-slate-200/50" />

            <div className="bg-white p-12 rounded-3xl shadow-2xl w-full max-w-[460px] relative z-10 border border-slate-100 flex flex-col items-center">

                {/* Logo Section */}
                <div className="mb-8 flex flex-col items-center">
                    <div className="w-20 h-20 bg-blue-50 rounded-2xl flex items-center justify-center border-2 border-blue-100 mb-5 shadow-sm">
                        <img src="/manager_icon.png" alt="Logo" className="w-12 h-12 object-contain" onError={(e) => e.target.style.display = 'none'} />
                        {/* Fallback Icon if logo missing */}
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none" style={{ display: 'none' }}>
                            <Lock className="text-blue-600" size={32} />
                        </div>
                    </div>
                    <h1 className="text-[28px] font-bold text-slate-900 tracking-tight text-center mb-1">Competence CRM</h1>
                    <p className="text-slate-500 font-medium text-[15px]">Sign in to your account</p>
                </div>

                <form onSubmit={handleLogin} className="w-full space-y-5">
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2 ml-1">Email Address</label>
                        <input
                            type="email"
                            required
                            className="w-full px-4 py-3.5 rounded-xl border-2 border-slate-200 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all font-medium"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2 ml-1">Password</label>
                        <div className="relative">
                            <input
                                type={showPassword ? "text" : "password"}
                                required
                                className="w-full px-4 py-3.5 rounded-xl border-2 border-slate-200 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all font-medium pr-12"
                                placeholder="Enter your password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 cursor-pointer"
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-blue-600/30 active:scale-[0.98] transition-all flex items-center justify-center gap-2 mt-2 text-[16px]"
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>
                                <ArrowRight size={18} strokeWidth={2.5} />
                                Sign In
                            </>
                        )}
                    </button>
                </form>

                <div className="mt-6">
                    <button
                        type="button"
                        onClick={() => alert("Please contact your manager to reset your password.")}
                        className="text-blue-600 hover:text-blue-700 font-semibold text-sm hover:underline transition-all"
                    >
                        Forgot your password?
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Login;
