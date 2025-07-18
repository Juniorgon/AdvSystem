import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

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
  const [loading, setLoading] = useState(false);

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

  useEffect(() => {
    fetchDashboardData();
    fetchClients();
    fetchProcesses();
    fetchFinancialTransactions();
    fetchContracts();
  }, []);

  // Navigation Component
  const Navigation = () => (
    <nav className="bg-gray-900 border-b border-gray-800 p-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-white">
            <span className="text-orange-500">GB</span> Advocacia & N. Comin
          </h1>
        </div>
        <div className="flex space-x-1">
          {[
            { key: 'dashboard', label: 'Dashboard', icon: '📊' },
            { key: 'clients', label: 'Clientes', icon: '👥' },
            { key: 'processes', label: 'Processos', icon: '⚖️' },
            { key: 'financial', label: 'Financeiro', icon: '💰' },
            { key: 'contracts', label: 'Contratos', icon: '📋' }
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
      </div>
    </nav>
  );

  // Dashboard Component
  const Dashboard = () => (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Clientes</p>
              <p className="text-2xl font-bold text-white">{dashboardStats.total_clients || 0}</p>
            </div>
            <div className="text-orange-500 text-3xl">👥</div>
          </div>
        </div>
        
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Processos</p>
              <p className="text-2xl font-bold text-white">{dashboardStats.total_processes || 0}</p>
            </div>
            <div className="text-orange-500 text-3xl">⚖️</div>
          </div>
        </div>
        
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Receita Total</p>
              <p className="text-2xl font-bold text-green-400">
                R$ {dashboardStats.total_revenue?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) || '0,00'}
              </p>
            </div>
            <div className="text-green-500 text-3xl">📈</div>
          </div>
        </div>
        
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Despesas Total</p>
              <p className="text-2xl font-bold text-red-400">
                R$ {dashboardStats.total_expenses?.toLocaleString('pt-BR', {minimumFractionDigits: 2}) || '0,00'}
              </p>
            </div>
            <div className="text-red-500 text-3xl">📉</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Pagamentos Pendentes</p>
              <p className="text-2xl font-bold text-yellow-400">{dashboardStats.pending_payments || 0}</p>
            </div>
            <div className="text-yellow-500 text-3xl">⏳</div>
          </div>
        </div>
        
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Pagamentos Vencidos</p>
              <p className="text-2xl font-bold text-red-400">{dashboardStats.overdue_payments || 0}</p>
            </div>
            <div className="text-red-500 text-3xl">🚨</div>
          </div>
        </div>
        
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
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
        
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
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

      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Resumo do Fluxo de Caixa</h3>
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-gray-400">Saldo Atual:</span>
            <span className={`text-xl font-bold ${
              (dashboardStats.total_revenue - dashboardStats.total_expenses) >= 0 
                ? 'text-green-400' 
                : 'text-red-400'
            }`}>
              R$ {((dashboardStats.total_revenue || 0) - (dashboardStats.total_expenses || 0))
                .toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-400">Saldo Mensal:</span>
            <span className={`text-xl font-bold ${
              (dashboardStats.monthly_revenue - dashboardStats.monthly_expenses) >= 0 
                ? 'text-green-400' 
                : 'text-red-400'
            }`}>
              R$ {((dashboardStats.monthly_revenue || 0) - (dashboardStats.monthly_expenses || 0))
                .toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  // Clients Component
  const Clients = () => {
    const [showForm, setShowForm] = useState(false);
    const [selectedClientId, setSelectedClientId] = useState(null);
    const [clientProcesses, setClientProcesses] = useState([]);
    const [showProcesses, setShowProcesses] = useState(false);
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
        await axios.post(`${API}/clients`, formData);
        setShowForm(false);
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
        await fetchClients();
      } catch (error) {
        console.error('Error creating client:', error);
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

    return (
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-white">Clientes</h2>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {showForm ? 'Cancelar' : 'Novo Cliente'}
          </button>
        </div>

        {showForm && (
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Novo Cliente</h3>
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
              
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Salvando...' : 'Salvar Cliente'}
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
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

  // Simple placeholder components for other sections
  const Processes = () => (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-white mb-4">Processos</h2>
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <p className="text-gray-300">Total de processos: {processes.length}</p>
        <p className="text-gray-400 mt-2">Funcionalidade em desenvolvimento...</p>
      </div>
    </div>
  );

  const Financial = () => (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-white mb-4">Financeiro</h2>
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <p className="text-gray-300">Total de transações: {financialTransactions.length}</p>
        <p className="text-gray-400 mt-2">Funcionalidade em desenvolvimento...</p>
      </div>
    </div>
  );

  const Contracts = () => (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-white mb-4">Contratos</h2>
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <p className="text-gray-300">Total de contratos: {contracts.length}</p>
        <p className="text-gray-400 mt-2">Funcionalidade em desenvolvimento...</p>
      </div>
    </div>
  );

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
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <Navigation />
      <main className="max-w-7xl mx-auto">
        {renderCurrentPage()}
      </main>
    </div>
  );
}

export default App;