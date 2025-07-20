import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import html2canvas from 'html2canvas';
import { saveAs } from 'file-saver';
import * as XLSX from 'xlsx';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
  ArcElement
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Main App Component
function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [dashboardStats, setDashboardStats] = useState({});
  const [clients, setClients] = useState([]);
  const [processes, setProcesses] = useState([]);
  const [financialTransactions, setFinancialTransactions] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [lawyers, setLawyers] = useState([]);
  const [loading, setLoading] = useState(false);

  // Authentication State
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [loginForm, setLoginForm] = useState({ username_or_email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    role: 'lawyer',
    branch_id: ''
  });

  // Check authentication on component mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    if (token && userData) {
      setUser(JSON.parse(userData));
      setIsAuthenticated(true);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  // Authentication functions
  const login = async (credentials) => {
    try {
      const response = await axios.post(`${API}/auth/login`, credentials);
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      
      setUser(userData);
      setIsAuthenticated(true);
      setShowLogin(false);
      
      // Set default authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      toast.success(`Bem-vindo, ${userData.full_name}!`);
    } catch (error) {
      handleApiError(error, 'Erro no login. Verifique suas credenciais.');
    }
  };

  const register = async (userData) => {
    try {
      await axios.post(`${API}/auth/register`, userData);
      toast.success('Usuário registrado com sucesso! Faça login para continuar.');
      setShowRegister(false);
      setShowLogin(true);
    } catch (error) {
      handleApiError(error, 'Erro no registro. Tente novamente.');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    setIsAuthenticated(false);
    setCurrentPage('dashboard');
  };

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    login(loginForm);
  };

  const handleRegisterSubmit = (e) => {
    e.preventDefault();
    register(registerForm);
  };

  // Generic error handler for better user feedback
  const handleApiError = (error, defaultMessage) => {
    console.error('API Error:', error);
    
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data?.message;
      
      switch (status) {
        case 400:
          toast.error(detail || 'Dados inválidos. Verifique as informações e tente novamente.');
          break;
        case 401:
          toast.error('Sessão expirada. Faça login novamente.');
          logout();
          break;
        case 403:
          toast.error('Você não tem permissão para realizar esta ação.');
          break;
        case 404:
          toast.error(detail || 'Registro não encontrado.');
          break;
        case 409:
          toast.error(detail || 'Este registro já existe ou está em conflito.');
          break;
        case 422:
          toast.error('Dados inválidos. Verifique os campos obrigatórios.');
          break;
        case 500:
          toast.error('Erro interno do servidor. Tente novamente em alguns minutos.');
          break;
        default:
          toast.error(detail || defaultMessage || 'Erro inesperado. Tente novamente.');
      }
    } else if (error.request) {
      toast.error('Erro de conexão. Verifique sua internet e tente novamente.');
    } else {
      toast.error(defaultMessage || 'Erro inesperado. Tente novamente.');
    }
  };

  // Export Functions
  const exportToPDF = async (data, title, filename) => {
    const doc = new jsPDF();
    
    // Add title
    doc.setFontSize(20);
    doc.text(title, 20, 20);
    
    // Add company info
    doc.setFontSize(12);
    doc.text('GB Advocacia & N. Comin', 20, 35);
    doc.text(`Relatório gerado em: ${new Date().toLocaleDateString('pt-BR')}`, 20, 45);
    
    // Add table based on data type
    if (data.length > 0) {
      let columns = [];
      let rows = [];
      
      if (title.includes('Cliente')) {
        columns = ['Nome', 'Tipo', 'CPF/CNPJ', 'Cidade', 'Telefone'];
        rows = data.map(item => [
          item.name,
          item.client_type === 'individual' ? 'Pessoa Física' : 'Pessoa Jurídica',
          item.cpf,
          item.address?.city || '',
          item.phone
        ]);
      } else if (title.includes('Advogado')) {
        columns = ['Nome', 'OAB', 'Email', 'Telefone', 'Especialização'];
        rows = data.map(item => [
          item.full_name,
          `${item.oab_number}/${item.oab_state}`,
          item.email,
          item.phone,
          item.specialization || 'Não informado'
        ]);
      } else if (title.includes('Processo')) {
        columns = ['Número', 'Tipo', 'Cliente', 'Status', 'Valor'];
        rows = data.map(item => [
          item.process_number,
          item.type,
          clients.find(c => c.id === item.client_id)?.name || '',
          item.status,
          `R$ ${item.value?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) || '0,00'}`
        ]);
      } else if (title.includes('Financeiro')) {
        columns = ['Tipo', 'Descrição', 'Valor', 'Status', 'Vencimento'];
        rows = data.map(item => [
          item.type === 'receita' ? 'Receita' : 'Despesa',
          item.description,
          `R$ ${item.value?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) || '0,00'}`,
          item.status,
          new Date(item.due_date).toLocaleDateString('pt-BR')
        ]);
      } else if (title.includes('Contrato')) {
        columns = ['Cliente', 'Título', 'Valor', 'Status', 'Parcelas'];
        rows = data.map(item => [
          clients.find(c => c.id === item.client_id)?.name || '',
          item.title,
          `R$ ${item.value?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) || '0,00'}`,
          item.status,
          `${item.installments}x`
        ]);
      }
      
      doc.autoTable({
        startY: 60,
        head: [columns],
        body: rows,
        theme: 'striped',
        styles: { fontSize: 8 },
        headStyles: { fillColor: [234, 88, 12] }
      });
    }
    
    doc.save(filename);
    toast.success('Relatório PDF gerado com sucesso!');
  };

  const exportToExcel = (data, title, filename) => {
    let processedData = [];
    
    if (title.includes('Cliente')) {
      processedData = data.map(item => ({
        'Nome': item.name,
        'Tipo': item.client_type === 'individual' ? 'Pessoa Física' : 'Pessoa Jurídica',
        'CPF/CNPJ': item.cpf,
        'Nacionalidade': item.nationality,
        'Estado Civil': item.civil_status,
        'Profissão': item.profession,
        'Telefone': item.phone,
        'Rua': item.address?.street,
        'Número': item.address?.number,
        'Cidade': item.address?.city,
        'Estado': item.address?.state
      }));
    } else if (title.includes('Advogado')) {
      processedData = data.map(item => ({
        'Nome Completo': item.full_name,
        'Número OAB': item.oab_number,
        'Estado OAB': item.oab_state,
        'OAB Completa': `${item.oab_number}/${item.oab_state}`,
        'Email': item.email,
        'Telefone': item.phone,
        'Especialização': item.specialization || 'Não informado',
        'Status': item.is_active ? 'Ativo' : 'Inativo',
        'Data de Registro': new Date(item.created_at).toLocaleDateString('pt-BR')
      }));
    } else if (title.includes('Processo')) {
      processedData = data.map(item => ({
        'Número do Processo': item.process_number,
        'Tipo': item.type,
        'Cliente': clients.find(c => c.id === item.client_id)?.name || '',
        'Status': item.status,
        'Valor': item.value,
        'Descrição': item.description,
        'Posição': item.role === 'creditor' ? 'Credor' : 'Devedor'
      }));
    } else if (title.includes('Financeiro')) {
      processedData = data.map(item => ({
        'Tipo': item.type === 'receita' ? 'Receita' : 'Despesa',
        'Descrição': item.description,
        'Valor': item.value,
        'Status': item.status,
        'Categoria': item.category,
        'Vencimento': new Date(item.due_date).toLocaleDateString('pt-BR')
      }));
    } else if (title.includes('Contrato')) {
      processedData = data.map(item => ({
        'Cliente': clients.find(c => c.id === item.client_id)?.name || '',
        'Título': item.title,
        'Descrição': item.description,
        'Valor': item.value,
        'Parcelas': item.installments,
        'Status': item.status,
        'Condições de Pagamento': item.payment_conditions,
        'Data Início': new Date(item.start_date).toLocaleDateString('pt-BR'),
        'Data Fim': new Date(item.end_date).toLocaleDateString('pt-BR')
      }));
    }
    
    const ws = XLSX.utils.json_to_sheet(processedData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, title);
    XLSX.writeFile(wb, filename);
    toast.success('Relatório Excel gerado com sucesso!');
  };

  const exportDashboardToPDF = async () => {
    try {
      const dashboardElement = document.querySelector('.dashboard-export');
      if (!dashboardElement) {
        toast.error('Erro ao capturar dashboard');
        return;
      }
      
      const canvas = await html2canvas(dashboardElement);
      const imgData = canvas.toDataURL('image/png');
      
      const doc = new jsPDF('l', 'mm', 'a4'); // landscape
      const imgWidth = 280;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      doc.addImage(imgData, 'PNG', 10, 20, imgWidth, imgHeight);
      doc.setFontSize(16);
      doc.text('Dashboard - GB Advocacia & N. Comin', 10, 15);
      doc.setFontSize(10);
      doc.text(`Gerado em: ${new Date().toLocaleString('pt-BR')}`, 10, 10);
      
      doc.save('dashboard-gb-advocacia.pdf');
      toast.success('Dashboard exportado com sucesso!');
    } catch (error) {
      console.error('Error exporting dashboard:', error);
      toast.error('Erro ao exportar dashboard');
    }
  };

  const backupData = async () => {
    try {
      const backupData = {
        clients: clients,
        processes: processes,
        financial_transactions: financialTransactions,
        contracts: contracts,
        dashboard_stats: dashboardStats,
        export_date: new Date().toISOString(),
        version: "1.0"
      };
      
      const blob = new Blob([JSON.stringify(backupData, null, 2)], {
        type: 'application/json'
      });
      
      saveAs(blob, `backup-gb-advocacia-${new Date().toISOString().split('T')[0]}.json`);
      toast.success('Backup dos dados realizado com sucesso!');
    } catch (error) {
      console.error('Error creating backup:', error);
      toast.error('Erro ao criar backup');
    }
  };

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  // Fetch clients
  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/clients`);
      setClients(response.data);
    } catch (error) {
      console.error('Error fetching clients:', error);
    }
  };

  // Fetch processes
  const fetchProcesses = async () => {
    try {
      const response = await axios.get(`${API}/processes`);
      setProcesses(response.data);
    } catch (error) {
      console.error('Error fetching processes:', error);
    }
  };

  // Fetch financial transactions
  const fetchFinancialTransactions = async () => {
    try {
      const response = await axios.get(`${API}/financial`);
      setFinancialTransactions(response.data);
    } catch (error) {
      console.error('Error fetching financial transactions:', error);
    }
  };

  // Fetch contracts
  const fetchContracts = async () => {
    try {
      const response = await axios.get(`${API}/contracts`);
      setContracts(response.data);
    } catch (error) {
      console.error('Error fetching contracts:', error);
    }
  };

  // Fetch lawyers
  const fetchLawyers = async () => {
    try {
      const response = await axios.get(`${API}/lawyers`);
      setLawyers(response.data);
    } catch (error) {
      console.error('Error fetching lawyers:', error);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchDashboardData();
      fetchClients();
      fetchProcesses();
      fetchFinancialTransactions();
      fetchContracts();
      fetchLawyers();
    }
  }, [isAuthenticated]);

  // Navigation Component
  const Navigation = () => (
    <nav className="bg-gray-900 border-b border-gray-800 p-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-white">
            <span className="text-orange-500">GB</span> Advocacia & N. Comin
          </h1>
        </div>
        
        {isAuthenticated ? (
          <div className="flex items-center space-x-4">
            <div className="flex space-x-1">
              {[
                { key: 'dashboard', label: 'Dashboard', icon: '📊' },
                { key: 'clients', label: 'Clientes', icon: '👥' },
                { key: 'processes', label: 'Processos', icon: '⚖️' },
                { key: 'financial', label: 'Financeiro', icon: '💰' },
                { key: 'contracts', label: 'Contratos', icon: '📋' },
                { key: 'lawyers', label: 'Advogados', icon: '👨‍💼' }
              ].map(item => (
                <button
                  key={item.key}
                  onClick={() => setCurrentPage(item.key)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === item.key
                      ? 'bg-orange-600 text-white'
                      : 'text-gray-300 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  {item.icon} {item.label}
                </button>
              ))}
            </div>
            
            <div className="flex items-center space-x-3 border-l border-gray-700 pl-4">
              <div className="text-right">
                <p className="text-white text-sm font-medium">{user?.full_name}</p>
                <p className="text-gray-400 text-xs">{user?.role}</p>
              </div>
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg text-sm transition-colors"
              >
                Sair
              </button>
            </div>
          </div>
        ) : (
          <div className="flex space-x-2">
            <button
              onClick={() => setShowLogin(true)}
              className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => setShowRegister(true)}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            >
              Registrar
            </button>
          </div>
        )}
      </div>
    </nav>
  );

  // Login Modal Component
  const LoginModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold text-white">Login</h3>
          <button
            onClick={() => setShowLogin(false)}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>
        
        <form onSubmit={handleLoginSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">Usuário</label>
            <input
              type="text"
              value={loginForm.username}
              onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">Senha</label>
            <input
              type="password"
              value={loginForm.password}
              onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              required
            />
          </div>
          
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setShowLogin(false)}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg transition-colors"
            >
              Entrar
            </button>
          </div>
        </form>
        
        <div className="mt-4 p-3 bg-blue-900 bg-opacity-30 border border-blue-600 rounded-lg">
          <p className="text-blue-200 text-sm">
            <strong>Usuário padrão:</strong><br/>
            Usuário: admin<br/>
            Senha: admin123
          </p>
        </div>
      </div>
    </div>
  );

  // Register Modal Component
  const RegisterModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold text-white">Registrar Usuário</h3>
          <button
            onClick={() => setShowRegister(false)}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>
        
        <form onSubmit={handleRegisterSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">Nome Completo</label>
            <input
              type="text"
              value={registerForm.full_name}
              onChange={(e) => setRegisterForm({...registerForm, full_name: e.target.value})}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">Usuário</label>
            <input
              type="text"
              value={registerForm.username}
              onChange={(e) => setRegisterForm({...registerForm, username: e.target.value})}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={registerForm.email}
              onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">Senha</label>
            <input
              type="password"
              value={registerForm.password}
              onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">Função</label>
            <select
              value={registerForm.role}
              onChange={(e) => setRegisterForm({...registerForm, role: e.target.value})}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
            >
              <option value="lawyer">Advogado</option>
              <option value="secretary">Secretário(a)</option>
              <option value="admin">Administrador</option>
            </select>
          </div>
          
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setShowRegister(false)}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg transition-colors"
            >
              Registrar
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  // Dashboard Component with Charts
  const Dashboard = () => {
    const [chartPeriod, setChartPeriod] = useState('month');
    
    // Chart configurations
    const chartOptions = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#9CA3AF'
          }
        },
        title: {
          display: false,
        },
      },
      scales: {
        y: {
          ticks: {
            color: '#9CA3AF'
          },
          grid: {
            color: '#374151'
          }
        },
        x: {
          ticks: {
            color: '#9CA3AF'
          },
          grid: {
            color: '#374151'
          }
        }
      }
    };

    // Revenue vs Expenses Line Chart
    const revenueExpenseData = {
      labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
      datasets: [
        {
          label: 'Receitas',
          data: [0, 0, 0, 0, 0, 0, dashboardStats.monthly_revenue || 0, 0, 0, 0, 0, 0],
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
        },
        {
          label: 'Despesas',
          data: [0, 0, 0, 0, 0, 0, dashboardStats.monthly_expenses || 0, 0, 0, 0, 0, 0],
          borderColor: '#EF4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          tension: 0.4,
        },
      ],
    };

    // Processes Status Doughnut Chart
    const processesData = {
      labels: ['Em Andamento', 'Concluídos', 'Suspensos'],
      datasets: [
        {
          data: [
            processes.filter(p => p.status === 'Em Andamento').length,
            processes.filter(p => p.status === 'Concluído').length,
            processes.filter(p => p.status === 'Suspenso').length
          ],
          backgroundColor: ['#F59E0B', '#10B981', '#EF4444'],
          borderColor: ['#D97706', '#059669', '#DC2626'],
          borderWidth: 2,
        },
      ],
    };

    // Financial Status Bar Chart
    const financialData = {
      labels: ['Pendentes', 'Vencidos', 'Pagos'],
      datasets: [
        {
          label: 'Quantidade',
          data: [
            dashboardStats.pending_payments || 0,
            dashboardStats.overdue_payments || 0,
            financialTransactions.filter(f => f.status === 'pago').length
          ],
          backgroundColor: ['#F59E0B', '#EF4444', '#10B981'],
          borderColor: ['#D97706', '#DC2626', '#059669'],
          borderWidth: 2,
        },
      ],
    };

    // Client Types Distribution
    const clientTypesData = {
      labels: ['Pessoa Física', 'Pessoa Jurídica'],
      datasets: [
        {
          data: [
            clients.filter(c => c.client_type === 'individual').length,
            clients.filter(c => c.client_type === 'corporate').length
          ],
          backgroundColor: ['#F97316', '#3B82F6'],
          borderColor: ['#EA580C', '#2563EB'],
          borderWidth: 2,
        },
      ],
    };

    return (
      <div className="p-6 space-y-6 dashboard-export">
        {/* Header with period selector and export buttons */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center space-y-4 lg:space-y-0">
          <h2 className="text-2xl font-bold text-white">Dashboard - GB Advocacia & N. Comin</h2>
          <div className="flex flex-wrap gap-2">
            <div className="flex space-x-2">
              <button
                onClick={() => setChartPeriod('week')}
                className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                  chartPeriod === 'week' 
                    ? 'bg-orange-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Semana
              </button>
              <button
                onClick={() => setChartPeriod('month')}
                className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                  chartPeriod === 'month' 
                    ? 'bg-orange-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Mês
              </button>
              <button
                onClick={() => setChartPeriod('year')}
                className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                  chartPeriod === 'year' 
                    ? 'bg-orange-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Ano
              </button>
            </div>
            
            {/* Export Buttons */}
            <div className="flex space-x-2 border-l border-gray-600 pl-2">
              <button
                onClick={exportDashboardToPDF}
                className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-lg text-sm transition-colors flex items-center space-x-1"
              >
                <span>📊</span>
                <span>PDF</span>
              </button>
              <button
                onClick={backupData}
                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-lg text-sm transition-colors flex items-center space-x-1"
              >
                <span>💾</span>
                <span>Backup</span>
              </button>
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="card-gradient-blue p-6 rounded-lg shadow-lg card-hover animate-fadeIn">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Total Clientes</p>
                <p className="text-3xl font-bold text-white">{dashboardStats.total_clients || 0}</p>
                <p className="text-blue-200 text-xs mt-1">Ativos no sistema</p>
              </div>
              <div className="text-white text-4xl animate-pulse">👥</div>
            </div>
          </div>
          
          <div className="card-gradient-purple p-6 rounded-lg shadow-lg card-hover animate-fadeIn" style={{animationDelay: '0.1s'}}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm">Total Processos</p>
                <p className="text-3xl font-bold text-white">{dashboardStats.total_processes || 0}</p>
                <p className="text-purple-200 text-xs mt-1">Em acompanhamento</p>
              </div>
              <div className="text-white text-4xl animate-pulse">⚖️</div>
            </div>
          </div>
          
          <div className="card-gradient-green p-6 rounded-lg shadow-lg card-hover animate-fadeIn" style={{animationDelay: '0.2s'}}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm">Receita Total</p>
                <p className="text-3xl font-bold text-white">
                  R$ {dashboardStats.total_revenue?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) || '0,00'}
                </p>
                <p className="text-green-200 text-xs mt-1">Acumulado</p>
              </div>
              <div className="text-white text-4xl animate-pulse">📈</div>
            </div>
          </div>
          
          <div className="card-gradient-red p-6 rounded-lg shadow-lg card-hover animate-fadeIn" style={{animationDelay: '0.3s'}}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-100 text-sm">Despesas Total</p>
                <p className="text-3xl font-bold text-white">
                  R$ {dashboardStats.total_expenses?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) || '0,00'}
                </p>
                <p className="text-red-200 text-xs mt-1">Acumulado</p>
              </div>
              <div className="text-white text-4xl animate-pulse">📉</div>
            </div>
          </div>
        </div>

        {/* Secondary KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-800 p-6 rounded-lg border border-yellow-500 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Pagamentos Pendentes</p>
                <p className="text-2xl font-bold text-yellow-400">{dashboardStats.pending_payments || 0}</p>
              </div>
              <div className="text-yellow-500 text-3xl">⏳</div>
            </div>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-red-500 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Pagamentos Vencidos</p>
                <p className="text-2xl font-bold text-red-400">{dashboardStats.overdue_payments || 0}</p>
              </div>
              <div className="text-red-500 text-3xl">🚨</div>
            </div>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-green-500 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Receita Mensal</p>
                <p className="text-2xl font-bold text-green-400">
                  R$ {dashboardStats.monthly_revenue?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) || '0,00'}
                </p>
              </div>
              <div className="text-green-500 text-3xl">📊</div>
            </div>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg border border-red-400 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Despesas Mensais</p>
                <p className="text-2xl font-bold text-red-400">
                  R$ {dashboardStats.monthly_expenses?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) || '0,00'}
                </p>
              </div>
              <div className="text-red-500 text-3xl">📊</div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Revenue vs Expenses Chart */}
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-lg card-hover animate-slideInLeft">
            <h3 className="text-lg font-semibold text-white mb-4">Receitas vs Despesas</h3>
            <div className="h-64">
              <Line data={revenueExpenseData} options={chartOptions} />
            </div>
          </div>

          {/* Processes Status Chart */}
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-lg card-hover animate-slideInRight">
            <h3 className="text-lg font-semibold text-white mb-4">Status dos Processos</h3>
            <div className="h-64">
              <Doughnut data={processesData} options={chartOptions} />
            </div>
          </div>

          {/* Financial Status Chart */}
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-lg card-hover animate-slideInLeft" style={{animationDelay: '0.2s'}}>
            <h3 className="text-lg font-semibold text-white mb-4">Status Financeiro</h3>
            <div className="h-64">
              <Bar data={financialData} options={chartOptions} />
            </div>
          </div>

          {/* Client Types Chart */}
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-lg card-hover animate-slideInRight" style={{animationDelay: '0.2s'}}>
            <h3 className="text-lg font-semibold text-white mb-4">Tipos de Cliente</h3>
            <div className="h-64">
              <Doughnut data={clientTypesData} options={chartOptions} />
            </div>
          </div>
        </div>

        {/* Cash Flow Summary - Enhanced */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-lg">
          <h3 className="text-lg font-semibold text-white mb-4">Resumo do Fluxo de Caixa</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-gray-700 rounded-lg">
                <span className="text-gray-300 font-medium">Saldo Atual:</span>
                <span className={`text-2xl font-bold ${
                  (dashboardStats.total_revenue - dashboardStats.total_expenses) >= 0 
                    ? 'text-green-400' 
                    : 'text-red-400'
                }`}>
                  R$ {((dashboardStats.total_revenue || 0) - (dashboardStats.total_expenses || 0))
                    .toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                </span>
              </div>
              <div className="flex justify-between items-center p-4 bg-gray-700 rounded-lg">
                <span className="text-gray-300 font-medium">Saldo Mensal:</span>
                <span className={`text-2xl font-bold ${
                  (dashboardStats.monthly_revenue - dashboardStats.monthly_expenses) >= 0 
                    ? 'text-green-400' 
                    : 'text-red-400'
                }`}>
                  R$ {((dashboardStats.monthly_revenue || 0) - (dashboardStats.monthly_expenses || 0))
                    .toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                </span>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-gray-700 rounded-lg">
                <span className="text-gray-300 font-medium">Total de Contratos:</span>
                <span className="text-xl font-bold text-blue-400">{contracts.length}</span>
              </div>
              <div className="flex justify-between items-center p-4 bg-gray-700 rounded-lg">
                <span className="text-gray-300 font-medium">Margem de Lucro:</span>
                <span className={`text-xl font-bold ${
                  (dashboardStats.total_revenue || 0) > 0
                    ? 'text-purple-400'
                    : 'text-gray-400'
                }`}>
                  {(dashboardStats.total_revenue || 0) > 0 
                    ? `${(((dashboardStats.total_revenue - dashboardStats.total_expenses) / dashboardStats.total_revenue) * 100).toFixed(1)}%`
                    : '0%'
                  }
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Clients Component
  const Clients = () => {
    const [showForm, setShowForm] = useState(false);
    const [selectedClientId, setSelectedClientId] = useState(null);
    const [clientProcesses, setClientProcesses] = useState([]);
    const [showProcesses, setShowProcesses] = useState(false);
    const [showProcuration, setShowProcuration] = useState(false);
    const [procurationData, setProcurationData] = useState('');
    const [selectedClient, setSelectedClient] = useState(null);
    const [editingClient, setEditingClient] = useState(null);
    const [formData, setFormData] = useState({
      name: '',
      nationality: '',
      civil_status: '',
      profession: '',
      cpf: '',
      address: {
        street: '',
        number: '',
        city: '',
        district: '',
        state: '',
        complement: ''
      },
      phone: '',
      client_type: 'individual'
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        setLoading(true);
        
        if (editingClient) {
          // Update existing client
          await axios.put(`${API}/clients/${editingClient.id}`, formData);
          toast.success('Cliente atualizado com sucesso!');
        } else {
          // Create new client
          await axios.post(`${API}/clients`, formData);
          toast.success('Cliente criado com sucesso!');
        }
        
        cancelEdit();
        await fetchClients();
        await fetchDashboardData();
      } catch (error) {
        console.error('Error saving client:', error);
        toast.error('Erro ao salvar cliente. Verifique os dados e tente novamente.');
      } finally {
        setLoading(false);
      }
    };

    const handleAddressChange = (field, value) => {
      setFormData(prev => ({
        ...prev,
        address: {
          ...prev.address,
          [field]: value
        }
      }));
    };

    const fetchClientProcesses = async (clientId) => {
      try {
        const response = await axios.get(`${API}/clients/${clientId}/processes`);
        setClientProcesses(response.data);
        setSelectedClientId(clientId);
        setShowProcesses(true);
      } catch (error) {
        console.error('Error fetching client processes:', error);
        setClientProcesses([]);
      }
    };

    const getProcessCount = (clientId) => {
      const clientProcessCount = processes.filter(p => p.client_id === clientId).length;
      return clientProcessCount;
    };

    const createSampleProcesses = async () => {
      if (clients.length === 0) {
        alert('Crie pelo menos um cliente primeiro!');
        return;
      }

      const sampleProcesses = [
        {
          client_id: clients[0].id,
          process_number: "0001234-56.2024.8.26.0100",
          type: "Ação de Cobrança",
          status: "Em Andamento",
          value: 15000.00,
          description: "Cobrança de honorários advocatícios",
          role: "creditor"
        },
        {
          client_id: clients[0].id,
          process_number: "0007890-12.2024.8.26.0200",
          type: "Ação Trabalhista",
          status: "Concluído",
          value: 8500.00,
          description: "Rescisão contratual e verbas trabalhistas",
          role: "debtor"
        }
      ];

      if (clients.length > 1) {
        sampleProcesses.push({
          client_id: clients[1].id,
          process_number: "0005678-90.2024.8.26.0300",
          type: "Ação Cível",
          status: "Em Andamento",
          value: 25000.00,
          description: "Indenização por danos morais e materiais",
          role: "creditor"
        });
      }

      try {
        setLoading(true);
        for (const processData of sampleProcesses) {
          await axios.post(`${API}/processes`, processData);
        }
        await fetchProcesses();
        alert('Processos de teste criados com sucesso!');
      } catch (error) {
        console.error('Error creating sample processes:', error);
        alert('Erro ao criar processos de teste');
      } finally {
        setLoading(false);
      }
    };

    const generateProcuration = (client) => {
      const template = `PROCURAÇÃO

OUTORGANTE: ${client.name}, ${client.client_type === 'individual' ? 'brasileiro' : 'empresa brasileira'}, ${client.civil_status !== 'N/A' ? client.civil_status : ''}, ${client.profession}, portador do CPF ${client.cpf}, residente e domiciliado à ${client.address.street}, ${client.address.number}, ${client.address.district}, ${client.address.city}-${client.address.state}${client.address.complement ? ', ' + client.address.complement : ''}.

OUTORGADO: GB ADVOCACIA & N. COMIN, sociedade de advogados, inscrita no CNPJ sob o nº ________________, com sede à ________________, representada neste ato por seus sócios.

PODERES: O outorgante confere ao outorgado amplos poderes para representá-lo em juízo ou fora dele, podendo propor ações, contestar, transigir, desistir, renunciar ao direito sobre que se funda a ação, receber e dar quitação, firmar compromissos, receber citação, confessar, reconhecer procedência do pedido, fazer acordos, pedir arquivamento, levantar alvarás, alçadas e depósitos, nomear prepostos, prestar depoimento pessoal, produzir provas, requerer medidas cautelares, interpor recursos, acompanhar diligências, enfim, praticar todos os atos necessários ao fiel desempenho do mandato.

FORO: Fica eleito o foro da Comarca de São Paulo para dirimir quaisquer questões oriundas desta procuração.

Local: ________________
Data: ________________

________________________________
${client.name}
${client.client_type === 'individual' ? 'Pessoa Física' : 'Representante Legal'}
CPF: ${client.cpf}

Testemunhas:
1. _______________________________
   Nome:
   CPF:

2. _______________________________
   Nome:
   CPF:`;

      setSelectedClient(client);
      setProcurationData(template);
      setShowProcuration(true);
    };

    const downloadProcuration = () => {
      const element = document.createElement('a');
      const file = new Blob([procurationData], { type: 'text/plain' });
      element.href = URL.createObjectURL(file);
      element.download = `procuracao_${selectedClient.name.replace(/\s+/g, '_')}.txt`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    };

    const printProcuration = () => {
      const printWindow = window.open('', '_blank');
      printWindow.document.write(`
        <html>
          <head>
            <title>Procuração - ${selectedClient.name}</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
              h1 { text-align: center; margin-bottom: 30px; }
              .content { white-space: pre-wrap; }
            </style>
          </head>
          <body>
            <div class="content">${procurationData}</div>
          </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
    };

    const editClient = (client) => {
      setEditingClient(client);
      setFormData({
        name: client.name,
        nationality: client.nationality,
        civil_status: client.civil_status,
        profession: client.profession,
        cpf: client.cpf,
        address: client.address,
        phone: client.phone,
        client_type: client.client_type
      });
      setShowForm(true);
    };

    const cancelEdit = () => {
      setEditingClient(null);
      setFormData({
        name: '',
        nationality: '',
        civil_status: '',
        profession: '',
        cpf: '',
        address: {
          street: '',
          number: '',
          city: '',
          district: '',
          state: '',
          complement: ''
        },
        phone: '',
        client_type: 'individual'
      });
      setShowForm(false);
    };

    const deleteClient = async (clientId, clientName) => {
      if (window.confirm(`Tem certeza que deseja excluir o cliente "${clientName}"? Esta ação não pode ser desfeita.`)) {
        try {
          setLoading(true);
          await axios.delete(`${API}/clients/${clientId}`);
          await fetchClients();
          await fetchDashboardData();
          toast.success('Cliente excluído com sucesso!');
        } catch (error) {
          handleApiError(error, 'Erro ao excluir cliente.');
        } finally {
          setLoading(false);
        }
      }
    };

    const createSampleFinancialData = async () => {
      const sampleTransactions = [
        {
          type: 'receita',
          description: 'Honorários advocatícios - Caso Maria Silva',
          value: 5000.00,
          due_date: new Date('2024-12-15').toISOString(),
          category: 'Honorários',
          client_id: clients.length > 0 ? clients[0].id : null
        },
        {
          type: 'receita',
          description: 'Sucumbência - Ação Trabalhista',
          value: 3500.00,
          due_date: new Date('2024-11-20').toISOString(),
          category: 'Sucumbência',
          client_id: clients.length > 1 ? clients[1].id : null
        },
        {
          type: 'despesa',
          description: 'Aluguel do escritório - Novembro',
          value: 4500.00,
          due_date: new Date('2024-11-05').toISOString(),
          category: 'Aluguel'
        },
        {
          type: 'despesa',
          description: 'Salário secretária',
          value: 2800.00,
          due_date: new Date('2024-11-30').toISOString(),
          category: 'Salários'
        },
        {
          type: 'despesa',
          description: 'Custas processuais - Processo 001234',
          value: 350.00,
          due_date: new Date('2024-10-15').toISOString(),
          category: 'Custas Processuais',
          status: 'pago'
        },
        {
          type: 'receita',
          description: 'Consultoria jurídica - Empresa XYZ',
          value: 1500.00,
          due_date: new Date('2024-09-30').toISOString(),
          category: 'Consultoria',
          status: 'pago'
        }
      ];

      try {
        setLoading(true);
        for (const transactionData of sampleTransactions) {
          await axios.post(`${API}/financial`, transactionData);
        }
        await fetchFinancialTransactions();
        await fetchDashboardData();
        alert('Dados financeiros de teste criados com sucesso!');
      } catch (error) {
        console.error('Error creating sample financial data:', error);
        alert('Erro ao criar dados financeiros de teste');
      } finally {
        setLoading(false);
      }
    };

    return (
      <div className="p-6 space-y-6">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center space-y-4 lg:space-y-0">
          <h2 className="text-2xl font-bold text-white">Clientes</h2>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={createSampleProcesses}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
            >
              Criar Processos de Teste
            </button>
            <button
              onClick={createSampleFinancialData}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
            >
              Criar Dados Financeiros
            </button>
            <button
              onClick={() => exportToPDF(clients, 'Relatório de Clientes', 'clientes-gb-advocacia.pdf')}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg transition-colors text-sm flex items-center space-x-1"
            >
              <span>📊</span>
              <span>PDF</span>
            </button>
            <button
              onClick={() => exportToExcel(clients, 'Relatório de Clientes', 'clientes-gb-advocacia.xlsx')}
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg transition-colors text-sm flex items-center space-x-1"
            >
              <span>📈</span>
              <span>Excel</span>
            </button>
            <button
              onClick={() => setShowForm(!showForm)}
              className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
            >
              {showForm ? 'Cancelar' : 'Novo Cliente'}
            </button>
          </div>
        </div>

        {showForm && (
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">
              {editingClient ? 'Editar Cliente' : 'Novo Cliente'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Nome Completo</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Tipo</label>
                  <select
                    value={formData.client_type}
                    onChange={(e) => setFormData({...formData, client_type: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="individual">Pessoa Física</option>
                    <option value="corporate">Pessoa Jurídica</option>
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Nacionalidade</label>
                  <input
                    type="text"
                    value={formData.nationality}
                    onChange={(e) => setFormData({...formData, nationality: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Estado Civil</label>
                  <input
                    type="text"
                    value={formData.civil_status}
                    onChange={(e) => setFormData({...formData, civil_status: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Profissão</label>
                  <input
                    type="text"
                    value={formData.profession}
                    onChange={(e) => setFormData({...formData, profession: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">CPF</label>
                  <input
                    type="text"
                    value={formData.cpf}
                    onChange={(e) => setFormData({...formData, cpf: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Telefone</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-4">
                <h4 className="text-md font-semibold text-white">Endereço</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Rua</label>
                    <input
                      type="text"
                      value={formData.address.street}
                      onChange={(e) => handleAddressChange('street', e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Número</label>
                    <input
                      type="text"
                      value={formData.address.number}
                      onChange={(e) => handleAddressChange('number', e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Cidade</label>
                    <input
                      type="text"
                      value={formData.address.city}
                      onChange={(e) => handleAddressChange('city', e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Bairro</label>
                    <input
                      type="text"
                      value={formData.address.district}
                      onChange={(e) => handleAddressChange('district', e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Estado</label>
                    <input
                      type="text"
                      value={formData.address.state}
                      onChange={(e) => handleAddressChange('state', e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Complemento</label>
                    <input
                      type="text"
                      value={formData.address.complement}
                      onChange={(e) => handleAddressChange('complement', e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    />
                  </div>
                </div>
              </div>
              
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={cancelEdit}
                    className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Salvando...' : editingClient ? 'Atualizar Cliente' : 'Salvar Cliente'}
                  </button>
                </div>
            </form>
          </div>
        )}

        {showProcesses && (
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">
                Processos do Cliente: {clients.find(c => c.id === selectedClientId)?.name}
              </h3>
              <button
                onClick={() => setShowProcesses(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕ Fechar
              </button>
            </div>
            
            {clientProcesses.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Número do Processo</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Tipo</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Status</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Valor</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Posição</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Descrição</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {clientProcesses.map((process) => (
                      <tr key={process.id} className="hover:bg-gray-700">
                        <td className="px-4 py-2 text-sm text-white font-medium">{process.process_number}</td>
                        <td className="px-4 py-2 text-sm text-gray-300">{process.type}</td>
                        <td className="px-4 py-2 text-sm">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            process.status === 'Em Andamento' ? 'bg-yellow-100 text-yellow-800' :
                            process.status === 'Concluído' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {process.status}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-sm text-green-400 font-medium">
                          R$ {process.value.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                        </td>
                        <td className="px-4 py-2 text-sm">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            process.role === 'creditor' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {process.role === 'creditor' ? 'Credor' : 'Devedor'}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-300 max-w-xs truncate">{process.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-400">Nenhum processo encontrado para este cliente</p>
              </div>
            )}
          </div>
        )}

        {/* Procuration Modal */}
        {showProcuration && selectedClient && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold text-white">
                  Procuração - {selectedClient.name}
                </h3>
                <div className="flex space-x-2">
                  <button
                    onClick={downloadProcuration}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    📄 Baixar
                  </button>
                  <button
                    onClick={printProcuration}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    🖨️ Imprimir
                  </button>
                  <button
                    onClick={() => setShowProcuration(false)}
                    className="text-gray-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="bg-gray-700 p-4 rounded-lg">
                  <p className="text-gray-300 text-sm mb-2">
                    <strong>Dados preenchidos automaticamente:</strong> Nome, Nacionalidade, Estado Civil, Profissão, CPF, Endereço
                  </p>
                  <p className="text-gray-300 text-sm">
                    <strong>Telefone excluído conforme solicitado.</strong> Edite o texto abaixo conforme necessário.
                  </p>
                </div>
                
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-2">
                    Texto da Procuração (Editável)
                  </label>
                  <textarea
                    value={procurationData}
                    onChange={(e) => setProcurationData(e.target.value)}
                    className="w-full h-96 p-4 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500 font-mono text-sm"
                    placeholder="Digite o texto da procuração..."
                  />
                </div>
                
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => setShowProcuration(false)}
                    className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={downloadProcuration}
                    className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Salvar e Baixar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Nome</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">CPF</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Telefone</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Cidade</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Processos</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {clients.map((client) => (
                  <tr key={client.id} className="hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{client.name}</div>
                      <div className="text-sm text-gray-400">{client.profession}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        client.client_type === 'individual' 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {client.client_type === 'individual' ? 'P. Física' : 'P. Jurídica'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{client.cpf}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{client.phone}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{client.address.city}/{client.address.state}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      <div className="flex items-center space-x-2">
                        <span className="bg-orange-100 text-orange-800 px-2 py-1 text-xs font-medium rounded-full">
                          {getProcessCount(client.id)} processos
                        </span>
                        {getProcessCount(client.id) > 0 && (
                          <button
                            onClick={() => fetchClientProcesses(client.id)}
                            className="text-orange-400 hover:text-orange-300 text-xs"
                          >
                            Ver
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => generateProcuration(client)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs transition-colors"
                        >
                          Gerar Procuração
                        </button>
                        <button 
                          onClick={() => editClient(client)}
                          className="text-orange-400 hover:text-orange-300"
                        >
                          Editar
                        </button>
                        <button 
                          onClick={() => deleteClient(client.id, client.name)}
                          className="text-red-400 hover:text-red-300"
                        >
                          Excluir
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Simple placeholder components for other sections
  const Processes = () => {
    const [showForm, setShowForm] = useState(false);
    const [filterStatus, setFilterStatus] = useState('all');
    const [filterType, setFilterType] = useState('all');
    const [filterClient, setFilterClient] = useState('all');
    const [selectedProcess, setSelectedProcess] = useState(null);
    const [showDetails, setShowDetails] = useState(false);
    const [formData, setFormData] = useState({
      client_id: '',
      process_number: '',
      type: '',
      status: 'Em Andamento',
      value: '',
      description: '',
      role: 'creditor'
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        setLoading(true);
        const processData = {
          ...formData,
          value: parseFloat(formData.value)
        };
        
        await axios.post(`${API}/processes`, processData);
        setShowForm(false);
        setFormData({
          client_id: '',
          process_number: '',
          type: '',
          status: 'Em Andamento',
          value: '',
          description: '',
          role: 'creditor'
        });
        await fetchProcesses();
      } catch (error) {
        console.error('Error creating process:', error);
        alert('Erro ao criar processo. Verifique os dados e tente novamente.');
      } finally {
        setLoading(false);
      }
    };

    const updateProcessStatus = async (processId, newStatus) => {
      try {
        await axios.put(`${API}/processes/${processId}`, { status: newStatus });
        await fetchProcesses();
      } catch (error) {
        console.error('Error updating process status:', error);
      }
    };

    const showProcessDetails = (process) => {
      setSelectedProcess(process);
      setShowDetails(true);
    };

    const generateProcessNumber = () => {
      const year = new Date().getFullYear();
      const random = Math.floor(Math.random() * 900000) + 100000;
      const processNumber = `${random.toString().substring(0,7)}-${Math.floor(Math.random() * 90) + 10}.${year}.8.26.${Math.floor(Math.random() * 9000) + 1000}`;
      setFormData({...formData, process_number: processNumber});
    };

    const createSampleProcessesAdvanced = async () => {
      if (clients.length === 0) {
        alert('Crie pelo menos um cliente primeiro!');
        return;
      }

      const processTypes = [
        'Ação de Cobrança',
        'Ação Trabalhista', 
        'Ação Cível',
        'Ação de Indenização',
        'Execução Fiscal',
        'Ação Penal',
        'Divórcio',
        'Inventário',
        'Usucapião',
        'Revisional de Contrato'
      ];

      const processStatuses = ['Em Andamento', 'Suspenso', 'Concluído', 'Arquivado'];
      const descriptions = [
        'Cobrança de honorários advocatícios em aberto',
        'Rescisão contratual e verbas trabalhistas',
        'Indenização por danos morais e materiais',
        'Execução de título executivo judicial',
        'Ação penal por crime contra o patrimônio',
        'Divórcio consensual com partilha de bens',
        'Inventário com múltiplos herdeiros',
        'Usucapião de bem imóvel urbano',
        'Revisão de contrato bancário',
        'Ação de despejo por falta de pagamento'
      ];

      const sampleProcesses = [];
      for (let i = 0; i < 8; i++) {
        const year = new Date().getFullYear();
        const random = Math.floor(Math.random() * 900000) + 100000;
        const processNumber = `${random.toString().substring(0,7)}-${Math.floor(Math.random() * 90) + 10}.${year}.8.26.${Math.floor(Math.random() * 9000) + 1000}`;
        
        sampleProcesses.push({
          client_id: clients[i % clients.length].id,
          process_number: processNumber,
          type: processTypes[i % processTypes.length],
          status: processStatuses[i % processStatuses.length],
          value: Math.floor(Math.random() * 50000) + 5000,
          description: descriptions[i % descriptions.length],
          role: i % 2 === 0 ? 'creditor' : 'debtor'
        });
      }

      try {
        setLoading(true);
        for (const processData of sampleProcesses) {
          await axios.post(`${API}/processes`, processData);
        }
        await fetchProcesses();
        alert('Processos avançados criados com sucesso!');
      } catch (error) {
        console.error('Error creating advanced processes:', error);
        alert('Erro ao criar processos avançados');
      } finally {
        setLoading(false);
      }
    };

    const filteredProcesses = processes.filter(process => {
      const statusMatch = filterStatus === 'all' || process.status === filterStatus;
      const typeMatch = filterType === 'all' || process.type === filterType;
      const clientMatch = filterClient === 'all' || process.client_id === filterClient;
      return statusMatch && typeMatch && clientMatch;
    });

    const getStatusColor = (status) => {
      switch(status) {
        case 'Em Andamento': return 'bg-yellow-100 text-yellow-800';
        case 'Concluído': return 'bg-green-100 text-green-800';
        case 'Suspenso': return 'bg-orange-100 text-orange-800';
        case 'Arquivado': return 'bg-gray-100 text-gray-800';
        default: return 'bg-blue-100 text-blue-800';
      }
    };

    const getRoleColor = (role) => {
      return role === 'creditor' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
    };

    const getClientName = (clientId) => {
      const client = clients.find(c => c.id === clientId);
      return client ? client.name : 'Cliente não encontrado';
    };

    const processStats = {
      total: processes.length,
      inProgress: processes.filter(p => p.status === 'Em Andamento').length,
      completed: processes.filter(p => p.status === 'Concluído').length,
      suspended: processes.filter(p => p.status === 'Suspenso').length,
      archived: processes.filter(p => p.status === 'Arquivado').length,
      totalValue: processes.reduce((sum, p) => sum + p.value, 0),
      averageValue: processes.length > 0 ? processes.reduce((sum, p) => sum + p.value, 0) / processes.length : 0
    };

    return (
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-white">Gestão de Processos</h2>
          <div className="flex space-x-2">
            <button
              onClick={createSampleProcessesAdvanced}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Criar Processos Avançados
            </button>
            <button
              onClick={() => setShowForm(!showForm)}
              className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              {showForm ? 'Cancelar' : 'Novo Processo'}
            </button>
          </div>
        </div>

        {/* Process Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400">Total Processos</h3>
            <p className="text-2xl font-bold text-white">{processStats.total}</p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400">Em Andamento</h3>
            <p className="text-2xl font-bold text-yellow-400">{processStats.inProgress}</p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400">Concluídos</h3>
            <p className="text-2xl font-bold text-green-400">{processStats.completed}</p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400">Suspensos</h3>
            <p className="text-2xl font-bold text-orange-400">{processStats.suspended}</p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400">Valor Total</h3>
            <p className="text-2xl font-bold text-blue-400">
              R$ {processStats.totalValue.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400">Valor Médio</h3>
            <p className="text-2xl font-bold text-purple-400">
              R$ {processStats.averageValue.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </p>
          </div>
        </div>

        {/* Process Form */}
        {showForm && (
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Novo Processo</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Cliente</label>
                  <select
                    value={formData.client_id}
                    onChange={(e) => setFormData({...formData, client_id: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  >
                    <option value="">Selecione um cliente...</option>
                    {clients.map(client => (
                      <option key={client.id} value={client.id}>{client.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Número do Processo</label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={formData.process_number}
                      onChange={(e) => setFormData({...formData, process_number: e.target.value})}
                      className="flex-1 p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                      placeholder="Ex: 1234567-89.2024.8.26.0100"
                      required
                    />
                    <button
                      type="button"
                      onClick={generateProcessNumber}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-md text-sm"
                    >
                      Gerar
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Tipo do Processo</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({...formData, type: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  >
                    <option value="">Selecione o tipo...</option>
                    <option value="Ação de Cobrança">Ação de Cobrança</option>
                    <option value="Ação Trabalhista">Ação Trabalhista</option>
                    <option value="Ação Cível">Ação Cível</option>
                    <option value="Ação de Indenização">Ação de Indenização</option>
                    <option value="Execução Fiscal">Execução Fiscal</option>
                    <option value="Ação Penal">Ação Penal</option>
                    <option value="Divórcio">Divórcio</option>
                    <option value="Inventário">Inventário</option>
                    <option value="Usucapião">Usucapião</option>
                    <option value="Revisional de Contrato">Revisional de Contrato</option>
                    <option value="Outros">Outros</option>
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="Em Andamento">Em Andamento</option>
                    <option value="Suspenso">Suspenso</option>
                    <option value="Concluído">Concluído</option>
                    <option value="Arquivado">Arquivado</option>
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Valor da Causa</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.value}
                    onChange={(e) => setFormData({...formData, value: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="0.00"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Posição do Cliente</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="creditor">Credor (Autor)</option>
                    <option value="debtor">Devedor (Réu)</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-1">Descrição</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  rows="3"
                  placeholder="Descreva o processo..."
                  required
                />
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Salvando...' : 'Salvar Processo'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Process Details Modal */}
        {showDetails && selectedProcess && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold text-white">Detalhes do Processo</h3>
                <button
                  onClick={() => setShowDetails(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-400">Número do Processo</h4>
                    <p className="text-white font-mono">{selectedProcess.process_number}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-400">Cliente</h4>
                    <p className="text-white">{getClientName(selectedProcess.client_id)}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-400">Tipo</h4>
                    <p className="text-white">{selectedProcess.type}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-400">Status</h4>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedProcess.status)}`}>
                      {selectedProcess.status}
                    </span>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-400">Valor da Causa</h4>
                    <p className="text-green-400 font-semibold">
                      R$ {selectedProcess.value.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-400">Posição</h4>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRoleColor(selectedProcess.role)}`}>
                      {selectedProcess.role === 'creditor' ? 'Credor (Autor)' : 'Devedor (Réu)'}
                    </span>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium text-gray-400 mb-2">Descrição</h4>
                  <p className="text-white bg-gray-700 p-3 rounded-md">{selectedProcess.description}</p>
                </div>
                
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => setShowDetails(false)}
                    className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Fechar
                  </button>
                  <button
                    onClick={() => {
                      // Here you could implement edit functionality
                      alert('Funcionalidade de edição em desenvolvimento');
                    }}
                    className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Editar Processo
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value="all">Todos</option>
                <option value="Em Andamento">Em Andamento</option>
                <option value="Suspenso">Suspenso</option>
                <option value="Concluído">Concluído</option>
                <option value="Arquivado">Arquivado</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Tipo</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value="all">Todos</option>
                <option value="Ação de Cobrança">Ação de Cobrança</option>
                <option value="Ação Trabalhista">Ação Trabalhista</option>
                <option value="Ação Cível">Ação Cível</option>
                <option value="Ação de Indenização">Ação de Indenização</option>
                <option value="Execução Fiscal">Execução Fiscal</option>
                <option value="Outros">Outros</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Cliente</label>
              <select
                value={filterClient}
                onChange={(e) => setFilterClient(e.target.value)}
                className="p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value="all">Todos</option>
                {clients.map(client => (
                  <option key={client.id} value={client.id}>{client.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Processes Table */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Processo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Cliente</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Valor</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Posição</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredProcesses.map((process) => (
                  <tr key={process.id} className="hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{process.process_number}</div>
                      <div className="text-sm text-gray-400 truncate max-w-xs">{process.description}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {getClientName(process.client_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{process.type}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(process.status)}`}>
                        {process.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-400">
                      R$ {process.value.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRoleColor(process.role)}`}>
                        {process.role === 'creditor' ? 'Credor' : 'Devedor'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => showProcessDetails(process)}
                          className="text-blue-400 hover:text-blue-300"
                        >
                          Ver
                        </button>
                        <button
                          onClick={() => updateProcessStatus(process.id, process.status === 'Em Andamento' ? 'Concluído' : 'Em Andamento')}
                          className="text-green-400 hover:text-green-300"
                        >
                          {process.status === 'Em Andamento' ? 'Concluir' : 'Reativar'}
                        </button>
                        <button className="text-orange-400 hover:text-orange-300">Editar</button>
                        <button className="text-red-400 hover:text-red-300">Excluir</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const Financial = () => {
    const [showForm, setShowForm] = useState(false);
    const [filterType, setFilterType] = useState('all');
    const [filterStatus, setFilterStatus] = useState('all');
    const [editingTransaction, setEditingTransaction] = useState(null);
    const [formData, setFormData] = useState({
      type: 'receita',
      description: '',
      value: '',
      due_date: '',
      category: '',
      client_id: '',
      process_id: ''
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        setLoading(true);
        const transactionData = {
          ...formData,
          value: parseFloat(formData.value),
          due_date: new Date(formData.due_date).toISOString(),
          client_id: formData.client_id || null,
          process_id: formData.process_id || null
        };
        
        if (editingTransaction) {
          await axios.put(`${API}/financial/${editingTransaction.id}`, transactionData);
          toast.success('Transação atualizada com sucesso!');
        } else {
          await axios.post(`${API}/financial`, transactionData);
          toast.success('Transação criada com sucesso!');
        }
        
        cancelEditTransaction();
        await fetchFinancialTransactions();
        await fetchDashboardData();
      } catch (error) {
        console.error('Error saving transaction:', error);
        alert('Erro ao salvar transação. Verifique os dados e tente novamente.');
      } finally {
        setLoading(false);
      }
    };

    const editTransaction = (transaction) => {
      setEditingTransaction(transaction);
      setFormData({
        type: transaction.type,
        description: transaction.description,
        value: transaction.value.toString(),
        due_date: new Date(transaction.due_date).toISOString().split('T')[0],
        category: transaction.category,
        client_id: transaction.client_id || '',
        process_id: transaction.process_id || ''
      });
      setShowForm(true);
    };

    const cancelEditTransaction = () => {
      setEditingTransaction(null);
      setFormData({
        type: 'receita',
        description: '',
        value: '',
        due_date: '',
        category: '',
        client_id: '',
        process_id: ''
      });
      setShowForm(false);
    };

    const deleteTransaction = async (transactionId, description) => {
      if (window.confirm(`Tem certeza que deseja excluir a transação "${description}"? Esta ação não pode ser desfeita.`)) {
        try {
          setLoading(true);
          await axios.delete(`${API}/financial/${transactionId}`);
          await fetchFinancialTransactions();
          await fetchDashboardData();
          toast.success('Transação excluída com sucesso!');
        } catch (error) {
          handleApiError(error, 'Erro ao excluir transação.');
        } finally {
          setLoading(false);
        }
      }
    };

    const markAsPaid = async (transactionId) => {
      try {
        await axios.put(`${API}/financial/${transactionId}`, {
          status: 'pago',
          payment_date: new Date().toISOString()
        });
        await fetchFinancialTransactions();
        await fetchDashboardData();
      } catch (error) {
        console.error('Error marking as paid:', error);
      }
    };

    const filteredTransactions = financialTransactions.filter(transaction => {
      const typeMatch = filterType === 'all' || transaction.type === filterType;
      const statusMatch = filterStatus === 'all' || transaction.status === filterStatus;
      return typeMatch && statusMatch;
    });

    const getStatusColor = (status) => {
      switch(status) {
        case 'pago': return 'bg-green-100 text-green-800';
        case 'pendente': return 'bg-yellow-100 text-yellow-800';
        case 'vencido': return 'bg-red-100 text-red-800';
        default: return 'bg-gray-100 text-gray-800';
      }
    };

    const getTypeColor = (type) => {
      return type === 'receita' ? 'text-green-400' : 'text-red-400';
    };

    return (
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-white">Controle Financeiro</h2>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {showForm ? 'Cancelar' : 'Nova Transação'}
          </button>
        </div>

        {/* Financial Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400">Total Receitas</h3>
            <p className="text-2xl font-bold text-green-400">
              R$ {financialTransactions
                .filter(t => t.type === 'receita')
                .reduce((sum, t) => sum + t.value, 0)
                .toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400">Total Despesas</h3>
            <p className="text-2xl font-bold text-red-400">
              R$ {financialTransactions
                .filter(t => t.type === 'despesa')
                .reduce((sum, t) => sum + t.value, 0)
                .toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400">A Receber</h3>
            <p className="text-2xl font-bold text-yellow-400">
              R$ {financialTransactions
                .filter(t => t.type === 'receita' && t.status === 'pendente')
                .reduce((sum, t) => sum + t.value, 0)
                .toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </p>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400">A Pagar</h3>
            <p className="text-2xl font-bold text-orange-400">
              R$ {financialTransactions
                .filter(t => t.type === 'despesa' && t.status === 'pendente')
                .reduce((sum, t) => sum + t.value, 0)
                .toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </p>
          </div>
        </div>

        {/* Transaction Form */}
        {showForm && (
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">
              {editingTransaction ? 'Editar Transação' : 'Nova Transação'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Tipo</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({...formData, type: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="receita">Receita</option>
                    <option value="despesa">Despesa</option>
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Valor</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.value}
                    onChange={(e) => setFormData({...formData, value: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Categoria</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  >
                    <option value="">Selecione...</option>
                    {formData.type === 'receita' ? (
                      <>
                        <option value="Honorários">Honorários</option>
                        <option value="Sucumbência">Sucumbência</option>
                        <option value="Consultoria">Consultoria</option>
                        <option value="Outros">Outros</option>
                      </>
                    ) : (
                      <>
                        <option value="Aluguel">Aluguel</option>
                        <option value="Salários">Salários</option>
                        <option value="Fornecedores">Fornecedores</option>
                        <option value="Impostos">Impostos</option>
                        <option value="Custas Processuais">Custas Processuais</option>
                        <option value="Outros">Outros</option>
                      </>
                    )}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Data de Vencimento</label>
                  <input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData({...formData, due_date: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Cliente (Opcional)</label>
                  <select
                    value={formData.client_id}
                    onChange={(e) => setFormData({...formData, client_id: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="">Selecione...</option>
                    {clients.map(client => (
                      <option key={client.id} value={client.id}>{client.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Processo (Opcional)</label>
                  <select
                    value={formData.process_id}
                    onChange={(e) => setFormData({...formData, process_id: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="">Selecione...</option>
                    {processes.map(process => (
                      <option key={process.id} value={process.id}>{process.process_number}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-1">Descrição</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  rows="3"
                  required
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={cancelEditTransaction}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Salvando...' : editingTransaction ? 'Atualizar Transação' : 'Salvar Transação'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Filters */}
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Tipo</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value="all">Todos</option>
                <option value="receita">Receitas</option>
                <option value="despesa">Despesas</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value="all">Todos</option>
                <option value="pendente">Pendente</option>
                <option value="pago">Pago</option>
                <option value="vencido">Vencido</option>
              </select>
            </div>
          </div>
        </div>

        {/* Transactions Table */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Descrição</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Valor</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Categoria</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Vencimento</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredTransactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        transaction.type === 'receita' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {transaction.type === 'receita' ? 'Receita' : 'Despesa'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{transaction.description}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <span className={getTypeColor(transaction.type)}>
                        R$ {transaction.value.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{transaction.category}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {new Date(transaction.due_date).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(transaction.status)}`}>
                        {transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {transaction.status === 'pendente' && (
                        <button
                          onClick={() => markAsPaid(transaction.id)}
                          className="text-green-400 hover:text-green-300 mr-3"
                        >
                          Marcar como Pago
                        </button>
                      )}
                      <button className="text-orange-400 hover:text-orange-300 mr-3">Editar</button>
                      <button className="text-red-400 hover:text-red-300">Excluir</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Enhanced Contracts Component
  const Contracts = () => {
    const [showForm, setShowForm] = useState(false);
    const [editingContract, setEditingContract] = useState(null);
    const [filterStatus, setFilterStatus] = useState('all');
    const [filterClient, setFilterClient] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [sortBy, setSortBy] = useState('created_at');
    const [sortOrder, setSortOrder] = useState('desc');
    const [showDetails, setShowDetails] = useState(false);
    const [selectedContract, setSelectedContract] = useState(null);
    const [formData, setFormData] = useState({
      client_id: '',
      title: '',
      description: '',
      value: '',
      payment_conditions: '',
      installments: 1,
      status: 'ativo',
      start_date: '',
      end_date: '',
      contract_type: 'honorarios',
      observations: ''
    });

    const contractTypes = [
      { value: 'honorarios', label: 'Honorários Advocatícios' },
      { value: 'consultoria', label: 'Consultoria Jurídica' },
      { value: 'assessoria', label: 'Assessoria Legal' },
      { value: 'representacao', label: 'Representação Processual' },
      { value: 'outros', label: 'Outros Serviços' }
    ];

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        setLoading(true);
        const contractData = {
          ...formData,
          value: parseFloat(formData.value),
          installments: parseInt(formData.installments),
          start_date: new Date(formData.start_date).toISOString(),
          end_date: new Date(formData.end_date).toISOString()
        };
        
        if (editingContract) {
          await axios.put(`${API}/contracts/${editingContract.id}`, contractData);
          toast.success('Contrato atualizado com sucesso!');
        } else {
          await axios.post(`${API}/contracts`, contractData);
          toast.success('Contrato criado com sucesso!');
        }
        
        resetForm();
        await fetchContracts();
        await fetchDashboardData();
      } catch (error) {
        handleApiError(error, 'Erro ao salvar contrato.');
      } finally {
        setLoading(false);
      }
    };

    const resetForm = () => {
      setShowForm(false);
      setFormData({
        client_id: '',
        title: '',
        description: '',
        value: '',
        payment_conditions: '',
        installments: 1,
        status: 'ativo',
        start_date: '',
        end_date: '',
        contract_type: 'honorarios',
        observations: ''
      });
      setEditingContract(null);
    };

    const editContract = (contract) => {
      setEditingContract(contract);
      setFormData({
        client_id: contract.client_id,
        title: contract.title,
        description: contract.description,
        value: contract.value.toString(),
        payment_conditions: contract.payment_conditions,
        installments: contract.installments.toString(),
        status: contract.status,
        start_date: new Date(contract.start_date).toISOString().split('T')[0],
        end_date: new Date(contract.end_date).toISOString().split('T')[0],
        contract_type: contract.contract_type || 'honorarios',
        observations: contract.observations || ''
      });
      setShowForm(true);
    };

    const deleteContract = async (contractId, contractTitle) => {
      if (window.confirm(`Tem certeza que deseja excluir o contrato "${contractTitle}"? Esta ação não pode ser desfeita.`)) {
        try {
          setLoading(true);
          await axios.delete(`${API}/contracts/${contractId}`);
          toast.success('Contrato excluído com sucesso!');
          await fetchContracts();
          await fetchDashboardData();
        } catch (error) {
          handleApiError(error, 'Erro ao excluir contrato.');
        } finally {
          setLoading(false);
        }
      }
    };

    const duplicateContract = async (contract) => {
      const duplicatedData = {
        ...contract,
        title: `${contract.title} (Cópia)`,
        status: 'rascunho',
        start_date: new Date().toISOString(),
        end_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString() // +1 year
      };
      delete duplicatedData.id;
      delete duplicatedData.created_at;
      delete duplicatedData.updated_at;

      try {
        setLoading(true);
        await axios.post(`${API}/contracts`, duplicatedData);
        toast.success('Contrato duplicado com sucesso!');
        await fetchContracts();
      } catch (error) {
        handleApiError(error, 'Erro ao duplicar contrato.');
      } finally {
        setLoading(false);
      }
    };

    const renewContract = async (contract) => {
      const renewedData = {
        ...contract,
        title: `${contract.title} - Renovação`,
        status: 'ativo',
        start_date: new Date().toISOString(),
        end_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString()
      };
      delete renewedData.id;
      delete renewedData.created_at;
      delete renewedData.updated_at;

      try {
        setLoading(true);
        await axios.post(`${API}/contracts`, renewedData);
        toast.success('Contrato renovado com sucesso!');
        await fetchContracts();
      } catch (error) {
        handleApiError(error, 'Erro ao renovar contrato.');
      } finally {
        setLoading(false);
      }
    };

    const getClientName = (clientId) => {
      const client = clients.find(c => c.id === clientId);
      return client ? client.name : 'Cliente não encontrado';
    };

    const getStatusColor = (status) => {
      switch(status) {
        case 'ativo': return 'bg-green-100 text-green-800';
        case 'concluído': return 'bg-blue-100 text-blue-800';
        case 'suspenso': return 'bg-yellow-100 text-yellow-800';
        case 'cancelado': return 'bg-red-100 text-red-800';
        case 'rascunho': return 'bg-gray-100 text-gray-800';
        default: return 'bg-gray-100 text-gray-800';
      }
    };

    const getContractTypeLabel = (type) => {
      const contractType = contractTypes.find(t => t.value === type);
      return contractType ? contractType.label : 'Tipo não informado';
    };

    // Filtered and sorted contracts
    const filteredContracts = contracts
      .filter(contract => {
        const statusMatch = filterStatus === 'all' || contract.status === filterStatus;
        const clientMatch = filterClient === 'all' || contract.client_id === filterClient;
        const searchMatch = searchTerm === '' || 
          contract.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          contract.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
          getClientName(contract.client_id).toLowerCase().includes(searchTerm.toLowerCase());
        return statusMatch && clientMatch && searchMatch;
      })
      .sort((a, b) => {
        const direction = sortOrder === 'asc' ? 1 : -1;
        switch(sortBy) {
          case 'client':
            return direction * getClientName(a.client_id).localeCompare(getClientName(b.client_id));
          case 'value':
            return direction * (a.value - b.value);
          case 'title':
            return direction * a.title.localeCompare(b.title);
          case 'status':
            return direction * a.status.localeCompare(b.status);
          case 'start_date':
            return direction * (new Date(a.start_date) - new Date(b.start_date));
          case 'end_date':
            return direction * (new Date(a.end_date) - new Date(b.end_date));
          default:
            return direction * (new Date(a.created_at) - new Date(b.created_at));
        }
      });

    const contractStats = {
      total: contracts.length,
      active: contracts.filter(c => c.status === 'ativo').length,
      completed: contracts.filter(c => c.status === 'concluído').length,
      suspended: contracts.filter(c => c.status === 'suspenso').length,
      cancelled: contracts.filter(c => c.status === 'cancelado').length,
      draft: contracts.filter(c => c.status === 'rascunho').length,
      totalValue: contracts.reduce((sum, c) => sum + (c.value || 0), 0),
      averageValue: contracts.length > 0 ? contracts.reduce((sum, c) => sum + (c.value || 0), 0) / contracts.length : 0,
      expiringSoon: contracts.filter(c => {
        const endDate = new Date(c.end_date);
        const now = new Date();
        const daysUntilExpiry = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
        return c.status === 'ativo' && daysUntilExpiry <= 30 && daysUntilExpiry > 0;
      }).length
    };

    return (
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center space-y-4 lg:space-y-0">
          <div>
            <h2 className="text-2xl font-bold text-white">📋 Gestão de Contratos</h2>
            <p className="text-gray-400 text-sm">Gerencie todos os contratos do escritório</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => exportToPDF(contracts, 'Relatório de Contratos', 'contratos-gb-advocacia.pdf')}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg transition-colors text-sm flex items-center space-x-1"
            >
              <span>📊</span>
              <span>PDF</span>
            </button>
            <button
              onClick={() => exportToExcel(contracts, 'Relatório de Contratos', 'contratos-gb-advocacia.xlsx')}
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg transition-colors text-sm flex items-center space-x-1"
            >
              <span>📈</span>
              <span>Excel</span>
            </button>
            <button
              onClick={() => setShowForm(true)}
              className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
            >
              Novo Contrato
            </button>
          </div>
        </div>

        {/* Enhanced Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          <div className="bg-blue-800 p-4 rounded-lg border border-blue-600 shadow-lg card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-xs">Total</p>
                <p className="text-xl font-bold text-white">{contractStats.total}</p>
              </div>
              <div className="text-blue-300 text-2xl">📋</div>
            </div>
          </div>
          
          <div className="bg-green-800 p-4 rounded-lg border border-green-600 shadow-lg card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-200 text-xs">Ativos</p>
                <p className="text-xl font-bold text-white">{contractStats.active}</p>
              </div>
              <div className="text-green-300 text-2xl">✅</div>
            </div>
          </div>
          
          <div className="bg-blue-700 p-4 rounded-lg border border-blue-500 shadow-lg card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-xs">Concluídos</p>
                <p className="text-xl font-bold text-white">{contractStats.completed}</p>
              </div>
              <div className="text-blue-300 text-2xl">🏁</div>
            </div>
          </div>
          
          <div className="bg-yellow-800 p-4 rounded-lg border border-yellow-600 shadow-lg card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-yellow-200 text-xs">Suspensos</p>
                <p className="text-xl font-bold text-white">{contractStats.suspended}</p>
              </div>
              <div className="text-yellow-300 text-2xl">⏸️</div>
            </div>
          </div>
          
          <div className="bg-purple-800 p-4 rounded-lg border border-purple-600 shadow-lg card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-xs">Valor Total</p>
                <p className="text-lg font-bold text-white">
                  R$ {(contractStats.totalValue / 1000).toFixed(0)}k
                </p>
              </div>
              <div className="text-purple-300 text-2xl">💰</div>
            </div>
          </div>
          
          <div className="bg-red-800 p-4 rounded-lg border border-red-600 shadow-lg card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-200 text-xs">Vencendo</p>
                <p className="text-xl font-bold text-white">{contractStats.expiringSoon}</p>
                <p className="text-red-300 text-xs">em 30 dias</p>
              </div>
              <div className="text-red-300 text-2xl">⚠️</div>
            </div>
          </div>
        </div>

        {/* Enhanced Filters and Search */}
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Buscar</label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Título, descrição ou cliente..."
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
              >
                <option value="all">Todos</option>
                <option value="ativo">Ativos</option>
                <option value="concluído">Concluídos</option>
                <option value="suspenso">Suspensos</option>
                <option value="cancelado">Cancelados</option>
                <option value="rascunho">Rascunhos</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Cliente</label>
              <select
                value={filterClient}
                onChange={(e) => setFilterClient(e.target.value)}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
              >
                <option value="all">Todos</option>
                {clients.map(client => (
                  <option key={client.id} value={client.id}>{client.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Ordenar por</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
              >
                <option value="created_at">Data de Criação</option>
                <option value="title">Título</option>
                <option value="client">Cliente</option>
                <option value="value">Valor</option>
                <option value="status">Status</option>
                <option value="start_date">Data Início</option>
                <option value="end_date">Data Fim</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Ordem</label>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
              >
                <option value="desc">Decrescente</option>
                <option value="asc">Crescente</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => {
                  setSearchTerm('');
                  setFilterStatus('all');
                  setFilterClient('all');
                  setSortBy('created_at');
                  setSortOrder('desc');
                }}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-lg transition-colors text-sm"
              >
                Limpar Filtros
              </button>
            </div>
          </div>
        </div>

        {/* Enhanced Contract Form */}
        {showForm && (
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-xl">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-white">
                {editingContract ? '✏️ Editar Contrato' : '➕ Novo Contrato'}
              </h3>
              <button
                onClick={resetForm}
                className="text-gray-400 hover:text-white text-xl"
              >
                ✕
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="bg-gray-750 p-4 rounded-lg border border-gray-600">
                <h4 className="text-lg font-medium text-white mb-4">📋 Informações Básicas</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Cliente *</label>
                    <select
                      value={formData.client_id}
                      onChange={(e) => setFormData({...formData, client_id: e.target.value})}
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      required
                    >
                      <option value="">Selecione um cliente</option>
                      {clients.map(client => (
                        <option key={client.id} value={client.id}>{client.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Tipo de Contrato *</label>
                    <select
                      value={formData.contract_type}
                      onChange={(e) => setFormData({...formData, contract_type: e.target.value})}
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      required
                    >
                      {contractTypes.map(type => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div className="mt-4">
                  <label className="block text-gray-300 text-sm font-medium mb-1">Título do Contrato *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    placeholder="Ex: Prestação de Serviços Advocatícios - Ação Trabalhista"
                    required
                  />
                </div>
                
                <div className="mt-4">
                  <label className="block text-gray-300 text-sm font-medium mb-1">Descrição Detalhada *</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    rows="4"
                    placeholder="Descreva os serviços, escopo do trabalho, responsabilidades..."
                    required
                  />
                </div>
              </div>

              {/* Financial Information */}
              <div className="bg-gray-750 p-4 rounded-lg border border-gray-600">
                <h4 className="text-lg font-medium text-white mb-4">💰 Informações Financeiras</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Valor Total (R$) *</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.value}
                      onChange={(e) => setFormData({...formData, value: e.target.value})}
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      placeholder="0.00"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Número de Parcelas *</label>
                    <input
                      type="number"
                      min="1"
                      max="60"
                      value={formData.installments}
                      onChange={(e) => setFormData({...formData, installments: e.target.value})}
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Status *</label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({...formData, status: e.target.value})}
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    >
                      <option value="rascunho">🗒️ Rascunho</option>
                      <option value="ativo">✅ Ativo</option>
                      <option value="suspenso">⏸️ Suspenso</option>
                      <option value="concluído">🏁 Concluído</option>
                      <option value="cancelado">❌ Cancelado</option>
                    </select>
                  </div>
                </div>

                <div className="mt-4">
                  <label className="block text-gray-300 text-sm font-medium mb-1">Condições de Pagamento *</label>
                  <input
                    type="text"
                    value={formData.payment_conditions}
                    onChange={(e) => setFormData({...formData, payment_conditions: e.target.value})}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    placeholder="Ex: 30% entrada + 70% em 6x mensais, vencimento dia 10"
                    required
                  />
                </div>
              </div>

              {/* Dates and Observations */}
              <div className="bg-gray-750 p-4 rounded-lg border border-gray-600">
                <h4 className="text-lg font-medium text-white mb-4">📅 Prazos e Observações</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Data de Início *</label>
                    <input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-1">Data de Término *</label>
                    <input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                      className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      required
                    />
                  </div>
                </div>
                
                <div className="mt-4">
                  <label className="block text-gray-300 text-sm font-medium mb-1">Observações Adicionais</label>
                  <textarea
                    value={formData.observations}
                    onChange={(e) => setFormData({...formData, observations: e.target.value})}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    rows="3"
                    placeholder="Observações importantes, cláusulas especiais, notas internas..."
                  />
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-3 pt-6 border-t border-gray-600">
                <button
                  type="button"
                  onClick={resetForm}
                  className="w-full sm:w-auto bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg transition-colors font-medium"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full sm:w-auto bg-orange-600 hover:bg-orange-700 text-white px-8 py-3 rounded-lg transition-colors disabled:opacity-50 font-medium flex items-center justify-center space-x-2"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Salvando...</span>
                    </>
                  ) : (
                    <span>{editingContract ? '✏️ Atualizar Contrato' : '➕ Criar Contrato'}</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Enhanced Contracts Table */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden shadow-xl">
          <div className="bg-gray-700 px-6 py-4 border-b border-gray-600">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-white">
                📋 Lista de Contratos ({filteredContracts.length})
              </h3>
              <div className="text-sm text-gray-400">
                {filteredContracts.length !== contracts.length && (
                  <span>Mostrando {filteredContracts.length} de {contracts.length}</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-750 sticky top-0">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Cliente</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Título</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Tipo</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Valor</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Parcelas</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Vigência</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredContracts.length > 0 ? (
                  filteredContracts.map((contract) => {
                    const endDate = new Date(contract.end_date);
                    const now = new Date();
                    const daysUntilExpiry = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
                    const isExpiring = contract.status === 'ativo' && daysUntilExpiry <= 30 && daysUntilExpiry > 0;
                    const isExpired = endDate < now && contract.status === 'ativo';

                    return (
                      <tr 
                        key={contract.id} 
                        className={`hover:bg-gray-700 transition-colors ${
                          isExpired ? 'bg-red-900 bg-opacity-20' : 
                          isExpiring ? 'bg-yellow-900 bg-opacity-20' : ''
                        }`}
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <div className="text-sm font-semibold text-white">
                              {getClientName(contract.client_id)}
                            </div>
                          </div>
                        </td>
                        
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-300 max-w-xs">
                            <div className="font-medium text-white truncate">{contract.title}</div>
                            <div className="text-xs text-gray-400 truncate mt-1">
                              {contract.description}
                            </div>
                          </div>
                        </td>
                        
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            {getContractTypeLabel(contract.contract_type)}
                          </span>
                        </td>
                        
                        <td className="px-6 py-4">
                          <div className="text-sm font-bold text-green-400">
                            R$ {contract.value?.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                          </div>
                          {contract.installments > 1 && (
                            <div className="text-xs text-gray-400">
                              {(contract.value / contract.installments).toLocaleString('pt-BR', {
                                style: 'currency',
                                currency: 'BRL'
                              })} / parcela
                            </div>
                          )}
                        </td>
                        
                        <td className="px-6 py-4">
                          <div className="flex items-center space-x-1">
                            <span className="text-sm font-medium text-white">{contract.installments}x</span>
                            {contract.installments > 1 && (
                              <span className="text-xs text-gray-400">parcelas</span>
                            )}
                          </div>
                        </td>
                        
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(contract.status)}`}>
                            {contract.status.charAt(0).toUpperCase() + contract.status.slice(1)}
                          </span>
                          {isExpiring && (
                            <div className="text-xs text-yellow-400 mt-1">
                              ⚠️ Vence em {daysUntilExpiry} dias
                            </div>
                          )}
                          {isExpired && (
                            <div className="text-xs text-red-400 mt-1">
                              🚨 Vencido há {Math.abs(daysUntilExpiry)} dias
                            </div>
                          )}
                        </td>
                        
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-300">
                            <div>{new Date(contract.start_date).toLocaleDateString('pt-BR')}</div>
                            <div className="text-xs text-gray-400">
                              até {new Date(contract.end_date).toLocaleDateString('pt-BR')}
                            </div>
                          </div>
                        </td>
                        
                        <td className="px-6 py-4">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => editContract(contract)}
                              className="text-blue-400 hover:text-blue-300 transition-colors p-1 rounded hover:bg-blue-900 hover:bg-opacity-20"
                              title="Editar contrato"
                            >
                              ✏️
                            </button>
                            
                            <button
                              onClick={() => duplicateContract(contract)}
                              className="text-purple-400 hover:text-purple-300 transition-colors p-1 rounded hover:bg-purple-900 hover:bg-opacity-20"
                              title="Duplicar contrato"
                            >
                              📋
                            </button>
                            
                            {contract.status === 'concluído' && (
                              <button
                                onClick={() => renewContract(contract)}
                                className="text-green-400 hover:text-green-300 transition-colors p-1 rounded hover:bg-green-900 hover:bg-opacity-20"
                                title="Renovar contrato"
                              >
                                🔄
                              </button>
                            )}
                            
                            <button
                              onClick={() => deleteContract(contract.id, contract.title)}
                              className="text-red-400 hover:text-red-300 transition-colors p-1 rounded hover:bg-red-900 hover:bg-opacity-20"
                              title="Excluir contrato"
                            >
                              🗑️
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan="8" className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center space-y-3">
                        <div className="text-4xl text-gray-500">📋</div>
                        <div className="text-lg font-medium text-gray-400">
                          {searchTerm || filterStatus !== 'all' || filterClient !== 'all' 
                            ? 'Nenhum contrato encontrado com os filtros aplicados' 
                            : 'Nenhum contrato cadastrado'
                          }
                        </div>
                        <div className="text-sm text-gray-500">
                          {searchTerm || filterStatus !== 'all' || filterClient !== 'all' 
                            ? 'Tente ajustar os filtros ou limpar a busca' 
                            : 'Clique em "Novo Contrato" para começar'
                          }
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Lawyers Component (Admin Only)
  const Lawyers = () => {
    const [showForm, setShowForm] = useState(false);
    const [editingLawyer, setEditingLawyer] = useState(null);
    const [formData, setFormData] = useState({
      full_name: '',
      oab_number: '',
      oab_state: 'SP',
      email: '',
      phone: '',
      specialization: ''
    });

    // Check if user is admin
    if (user?.role !== 'admin') {
      return (
        <div className="p-6">
          <div className="bg-red-900 bg-opacity-30 border border-red-600 rounded-lg p-6 text-center">
            <h2 className="text-2xl font-bold text-red-400 mb-4">🚫 Acesso Restrito</h2>
            <p className="text-red-200">
              Apenas administradores podem acessar a gestão de advogados.
            </p>
          </div>
        </div>
      );
    }

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        setLoading(true);
        
        if (editingLawyer) {
          await axios.put(`${API}/lawyers/${editingLawyer.id}`, formData);
          toast.success('Advogado atualizado com sucesso!');
        } else {
          await axios.post(`${API}/lawyers`, formData);
          toast.success('Advogado registrado com sucesso!');
        }
        
        setShowForm(false);
        setFormData({
          full_name: '',
          oab_number: '',
          oab_state: 'SP',
          email: '',
          phone: '',
          specialization: ''
        });
        setEditingLawyer(null);
        await fetchLawyers();
      } catch (error) {
        console.error('Error saving lawyer:', error);
        if (error.response?.status === 400) {
          toast.error(error.response.data.detail);
        } else {
          toast.error('Erro ao salvar advogado. Verifique os dados e tente novamente.');
        }
      } finally {
        setLoading(false);
      }
    };

    const editLawyer = (lawyer) => {
      setEditingLawyer(lawyer);
      setFormData({
        full_name: lawyer.full_name,
        oab_number: lawyer.oab_number,
        oab_state: lawyer.oab_state,
        email: lawyer.email,
        phone: lawyer.phone,
        specialization: lawyer.specialization
      });
      setShowForm(true);
    };

    const deactivateLawyer = async (lawyerId) => {
      if (window.confirm('Tem certeza que deseja desativar este advogado?')) {
        try {
          await axios.delete(`${API}/lawyers/${lawyerId}`);
          toast.success('Advogado desativado com sucesso!');
          await fetchLawyers();
        } catch (error) {
          console.error('Error deactivating lawyer:', error);
          toast.error('Erro ao desativar advogado.');
        }
      }
    };

    const lawyerStats = {
      total: lawyers.length,
      active: lawyers.filter(l => l.is_active).length,
      byState: lawyers.reduce((acc, lawyer) => {
        acc[lawyer.oab_state] = (acc[lawyer.oab_state] || 0) + 1;
        return acc;
      }, {})
    };

    const brazilianStates = [
      'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
      'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
      'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ];

    return (
      <div className="p-6 space-y-6">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center space-y-4 lg:space-y-0">
          <h2 className="text-2xl font-bold text-white">👨‍💼 Gestão de Advogados</h2>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => exportToPDF(lawyers, 'Relatório de Advogados', 'advogados-gb-advocacia.pdf')}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg transition-colors text-sm flex items-center space-x-1"
            >
              <span>📊</span>
              <span>PDF</span>
            </button>
            <button
              onClick={() => exportToExcel(lawyers, 'Relatório de Advogados', 'advogados-gb-advocacia.xlsx')}
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg transition-colors text-sm flex items-center space-x-1"
            >
              <span>📈</span>
              <span>Excel</span>
            </button>
            <button
              onClick={() => setShowForm(true)}
              className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
            >
              Registrar Advogado
            </button>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-blue-800 p-6 rounded-lg border border-blue-600 shadow-lg card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-sm">Total de Advogados</p>
                <p className="text-3xl font-bold text-white">{lawyerStats.total}</p>
              </div>
              <div className="text-blue-300 text-4xl">👨‍💼</div>
            </div>
          </div>
          
          <div className="bg-green-800 p-6 rounded-lg border border-green-600 shadow-lg card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-200 text-sm">Advogados Ativos</p>
                <p className="text-3xl font-bold text-white">{lawyerStats.active}</p>
              </div>
              <div className="text-green-300 text-4xl">✅</div>
            </div>
          </div>
          
          <div className="bg-purple-800 p-6 rounded-lg border border-purple-600 shadow-lg card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm">Estados Representados</p>
                <p className="text-3xl font-bold text-white">{Object.keys(lawyerStats.byState).length}</p>
              </div>
              <div className="text-purple-300 text-4xl">🗺️</div>
            </div>
          </div>
        </div>

        {/* Lawyer Form */}
        {showForm && (
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">
              {editingLawyer ? 'Editar Advogado' : 'Registrar Novo Advogado'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Nome Completo</label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Número OAB</label>
                  <input
                    type="text"
                    value={formData.oab_number}
                    onChange={(e) => setFormData({...formData, oab_number: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="123456"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Estado OAB</label>
                  <select
                    value={formData.oab_state}
                    onChange={(e) => setFormData({...formData, oab_state: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    required
                  >
                    {brazilianStates.map(state => (
                      <option key={state} value={state}>{state}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-1">Telefone</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="(11) 99999-9999"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 text-sm font-medium mb-1">Especialização (Opcional)</label>
                <input
                  type="text"
                  value={formData.specialization}
                  onChange={(e) => setFormData({...formData, specialization: e.target.value})}
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                  placeholder="Ex: Direito Tributário, Direito Trabalhista..."
                />
              </div>
              
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingLawyer(null);
                    setFormData({
                      full_name: '',
                      oab_number: '',
                      oab_state: 'SP',
                      email: '',
                      phone: '',
                      specialization: ''
                    });
                  }}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Salvando...' : editingLawyer ? 'Atualizar Advogado' : 'Registrar Advogado'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Lawyers Table */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Nome</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">OAB</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Email</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Telefone</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Especialização</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Status</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {lawyers.length > 0 ? (
                  lawyers.map((lawyer) => (
                    <tr key={lawyer.id} className="hover:bg-gray-700">
                      <td className="px-4 py-2 text-sm text-white font-medium">{lawyer.full_name}</td>
                      <td className="px-4 py-2 text-sm text-gray-300">
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 text-xs font-medium rounded-full">
                          {lawyer.oab_number}/{lawyer.oab_state}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-300">{lawyer.email}</td>
                      <td className="px-4 py-2 text-sm text-gray-300">{lawyer.phone}</td>
                      <td className="px-4 py-2 text-sm text-gray-300">
                        {lawyer.specialization || 'Não informado'}
                      </td>
                      <td className="px-4 py-2 text-sm">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          lawyer.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {lawyer.is_active ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm space-x-2">
                        <button
                          onClick={() => editLawyer(lawyer)}
                          className="text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          Editar
                        </button>
                        {lawyer.is_active && (
                          <button
                            onClick={() => deactivateLawyer(lawyer.id)}
                            className="text-red-400 hover:text-red-300 transition-colors"
                          >
                            Desativar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="px-4 py-8 text-center text-gray-400">
                      Nenhum advogado registrado
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const renderCurrentPage = () => {
    switch(currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'clients':
        return <Clients />;
      case 'processes':
        return <Processes />;
      case 'financial':
        return <Financial />;
      case 'contracts':
        return <Contracts />;
      case 'lawyers':
        return <Lawyers />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <Navigation />
      
      {isAuthenticated ? (
        <main className="max-w-7xl mx-auto">
          {renderCurrentPage()}
        </main>
      ) : (
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="text-center">
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                Sistema de Gestão Jurídica
              </h1>
              <p className="text-gray-300 text-lg">
                GB Advocacia & N. Comin - Controle completo do seu escritório
              </p>
            </div>
            
            <div className="bg-gray-800 p-8 rounded-lg border border-gray-700 max-w-md mx-auto">
              <h2 className="text-2xl font-semibold text-white mb-4">Bem-vindo!</h2>
              <p className="text-gray-400 mb-6">
                Faça login para acessar o sistema de gestão do escritório.
              </p>
              
              <div className="space-y-3">
                <button
                  onClick={() => setShowLogin(true)}
                  className="w-full bg-orange-600 hover:bg-orange-700 text-white py-3 rounded-lg font-medium transition-colors"
                >
                  Fazer Login
                </button>
                <button
                  onClick={() => setShowRegister(true)}
                  className="w-full bg-gray-600 hover:bg-gray-700 text-white py-3 rounded-lg font-medium transition-colors"
                >
                  Criar Conta
                </button>
              </div>
              
              <div className="mt-6 p-4 bg-blue-900 bg-opacity-30 border border-blue-600 rounded-lg">
                <p className="text-blue-200 text-sm">
                  <strong>Usuário de teste:</strong><br/>
                  Usuário: admin<br/>
                  Senha: admin123
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Modals */}
      {showLogin && <LoginModal />}
      {showRegister && <RegisterModal />}
      
      {/* Toast Container */}
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
    </div>
  );
}

export default App;