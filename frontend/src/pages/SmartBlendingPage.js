import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import ReactMarkdown from "react-markdown";
import {
  Sparkles,
  Flame,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Loader2,
  Database,
  Lightbulb,
  DollarSign
} from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
  Tooltip
} from "recharts";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SmartBlendingPage = () => {
  const { getAuthHeader } = useAuth();
  const [loading, setLoading] = useState(false);
  const [recommendation, setRecommendation] = useState(null);
  
  // Input states - default values from typical coal parameters
  const [targetGCV, setTargetGCV] = useState(4000);  // Typical: 4000 kcal/kg
  const [maxAsh, setMaxAsh] = useState(5.0);         // Typical: 5%
  const [maxSulphur, setMaxSulphur] = useState(1.8); // Typical: 1.8%
  const [maxTotalMoisture, setMaxTotalMoisture] = useState(35.0);  // Typical: 35%
  const [maxInherentMoisture, setMaxInherentMoisture] = useState(18.0);  // Typical: 18%
  const [minVolatileMatter, setMinVolatileMatter] = useState(35.0);  // Typical: 35%
  const [minFixedCarbon, setMinFixedCarbon] = useState(25.0);  // Typical: 25%
  const [targetQuantity, setTargetQuantity] = useState(10000);

  const handleGetRecommendation = async () => {
    setLoading(true);
    setRecommendation(null);
    
    try {
      const response = await axios.post(
        `${API_URL}/api/smart-blending/recommend`,
        {
          target_gcv: targetGCV,
          max_ash: maxAsh,
          max_sulphur: maxSulphur,
          max_total_moisture: maxTotalMoisture,
          max_inherent_moisture: maxInherentMoisture,
          min_volatile_matter: minVolatileMatter,
          min_fixed_carbon: minFixedCarbon,
          target_quantity: targetQuantity
        },
        { headers: getAuthHeader() }
      );

      setRecommendation(response.data);
      toast.success("AI recommendation generated successfully!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to get recommendation");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Prepare radar chart data
  const radarChartData = recommendation?.ai_recommendation?.predicted_quality ? [
    {
      metric: 'GCV',
      Target: targetGCV,
      Predicted: recommendation.ai_recommendation.predicted_quality.gcv,
      fullMark: 4700
    },
    {
      metric: 'Ash',
      Target: maxAsh,
      Predicted: recommendation.ai_recommendation.predicted_quality.ash,
      fullMark: 6
    },
    {
      metric: 'Sulphur',
      Target: maxSulphur,
      Predicted: recommendation.ai_recommendation.predicted_quality.sulphur,
      fullMark: 2.2
    },
    {
      metric: 'TM',
      Target: maxTotalMoisture,
      Predicted: recommendation.ai_recommendation.predicted_quality.total_moisture || 0,
      fullMark: 40
    },
    {
      metric: 'VM',
      Target: minVolatileMatter,
      Predicted: recommendation.ai_recommendation.predicted_quality.volatile_matter || 0,
      fullMark: 40
    },
    {
      metric: 'FC',
      Target: minFixedCarbon,
      Predicted: recommendation.ai_recommendation.predicted_quality.fixed_carbon || 0,
      fullMark: 41
    }
  ] : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            Smart Blending AI
          </h1>
          <p className="text-slate-400 mt-1">Optimalisasi Blending Batubara Berbasis AI</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <Card className="glass-card border-purple-500/30 lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Flame className="w-5 h-5 text-orange-400" />
              Parameter Target
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Target GCV Slider */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-slate-300">Target GCV (kcal/kg)</Label>
                <span className="text-cyan-400 font-mono font-semibold">{targetGCV}</span>
              </div>
              <Slider
                value={[targetGCV]}
                onValueChange={(val) => setTargetGCV(val[0])}
                min={3700}
                max={4700}
                step={50}
                className="py-4"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>3700</span>
                <span>4700</span>
              </div>
            </div>

            {/* Max Ash Slider */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-slate-300">Maksimal Kandungan Abu (%)</Label>
                <span className="text-yellow-400 font-mono font-semibold">{maxAsh.toFixed(1)}</span>
              </div>
              <Slider
                value={[maxAsh * 10]}
                onValueChange={(val) => setMaxAsh(val[0] / 10)}
                min={33}
                max={60}
                step={1}
                className="py-4"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>3.3%</span>
                <span>6.0%</span>
              </div>
            </div>

            {/* Max Sulphur Slider */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-slate-300">Maksimal Sulphur (%)</Label>
                <span className="text-red-400 font-mono font-semibold">{maxSulphur.toFixed(2)}</span>
              </div>
              <Slider
                value={[maxSulphur * 100]}
                onValueChange={(val) => setMaxSulphur(val[0] / 100)}
                min={13}
                max={220}
                step={1}
                className="py-4"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>0.13%</span>
                <span>2.2%</span>
              </div>
            </div>

            {/* Max Total Moisture Slider */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-slate-300">Maks. Total Moisture (%)</Label>
                <span className="text-blue-400 font-mono font-semibold">{maxTotalMoisture.toFixed(1)}</span>
              </div>
              <Slider
                value={[maxTotalMoisture * 10]}
                onValueChange={(val) => setMaxTotalMoisture(val[0] / 10)}
                min={250}
                max={400}
                step={5}
                className="py-4"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>25%</span>
                <span>40%</span>
              </div>
            </div>

            {/* Max Inherent Moisture Slider */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-slate-300">Maks. Inherent Moisture (%)</Label>
                <span className="text-indigo-400 font-mono font-semibold">{maxInherentMoisture.toFixed(1)}</span>
              </div>
              <Slider
                value={[maxInherentMoisture * 10]}
                onValueChange={(val) => setMaxInherentMoisture(val[0] / 10)}
                min={138}
                max={250}
                step={2}
                className="py-4"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>13.8%</span>
                <span>25%</span>
              </div>
            </div>

            {/* Min Volatile Matter Slider */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-slate-300">Min. Volatile Matter (%)</Label>
                <span className="text-green-400 font-mono font-semibold">{minVolatileMatter.toFixed(1)}</span>
              </div>
              <Slider
                value={[minVolatileMatter * 10]}
                onValueChange={(val) => setMinVolatileMatter(val[0] / 10)}
                min={279}
                max={400}
                step={5}
                className="py-4"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>27.9%</span>
                <span>40%</span>
              </div>
            </div>

            {/* Min Fixed Carbon Slider */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-slate-300">Min. Fixed Carbon (%)</Label>
                <span className="text-amber-400 font-mono font-semibold">{minFixedCarbon.toFixed(1)}</span>
              </div>
              <Slider
                value={[minFixedCarbon * 10]}
                onValueChange={(val) => setMinFixedCarbon(val[0] / 10)}
                min={230}
                max={410}
                step={5}
                className="py-4"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>23%</span>
                <span>41%</span>
              </div>
            </div>

            {/* Target Quantity Input */}
            <div className="space-y-2">
              <Label className="text-slate-300">Kuantitas Target (MT)</Label>
              <Input
                type="number"
                value={targetQuantity}
                onChange={(e) => setTargetQuantity(parseFloat(e.target.value))}
                className="bg-slate-800 border-slate-700 text-white font-mono"
              />
            </div>

            {/* Get Recommendation Button */}
            <Button
              onClick={handleGetRecommendation}
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  AI Sedang Menganalisis...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Dapatkan Rekomendasi AI
                </>
              )}
            </Button>

            {/* Data Sources Info */}
            {recommendation?.data_sources && (
              <div className="mt-4 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-4 h-4 text-blue-400" />
                  <span className="text-xs font-semibold text-slate-300">Sumber Data</span>
                </div>
                <div className="space-y-1 text-xs text-slate-400">
                  <div>• Vessel: {recommendation.data_sources.vessels_count}</div>
                  <div>• Barge: {recommendation.data_sources.barges_count}</div>
                  <div>• Trucking: {recommendation.data_sources.trucking_count}</div>
                  {recommendation.data_sources.latest_stock_date && (
                    <div className="text-cyan-400 mt-2">
                      Stock Terakhir: {new Date(recommendation.data_sources.latest_stock_date).toLocaleDateString('id-ID')}
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Panel */}
        <div className="lg:col-span-2 space-y-6">
          {!recommendation && !loading && (
            <Card className="glass-card border-white/10">
              <CardContent className="p-12 text-center">
                <Sparkles className="w-16 h-16 text-purple-400 mx-auto mb-4 opacity-50" />
                <h3 className="text-xl font-semibold text-white mb-2">
                  Optimalisasi Blending AI Siap
                </h3>
                <p className="text-slate-400 max-w-md mx-auto">
                  Atur parameter target Anda dan klik "Dapatkan Rekomendasi AI" untuk menerima formula blending batubara yang optimal dari Ahli Kimia Digital kami.
                </p>
              </CardContent>
            </Card>
          )}

          {loading && (
            <Card className="glass-card border-purple-500/30">
              <CardContent className="p-12 text-center">
                <Loader2 className="w-16 h-16 text-purple-400 mx-auto mb-4 animate-spin" />
                <h3 className="text-xl font-semibold text-white mb-2">
                  AI Sedang Menganalisis Inventori Batubara...
                </h3>
                <p className="text-slate-400">
                  Memproses data kualitas dan menghitung blend optimal
                </p>
              </CardContent>
            </Card>
          )}

          {recommendation?.ai_recommendation && !recommendation.ai_recommendation.error && (
            <>
              {/* Status Indicator */}
              <Card className={`glass-card ${recommendation.ai_recommendation.meets_target ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-yellow-500/30 bg-yellow-500/5'}`}>
                <CardContent className="p-4 flex items-center gap-3">
                  {recommendation.ai_recommendation.meets_target ? (
                    <>
                      <CheckCircle className="w-6 h-6 text-emerald-400" />
                      <div>
                        <p className="text-emerald-400 font-semibold">Target Tercapai!</p>
                        <p className="text-slate-400 text-sm">Blend yang direkomendasikan memenuhi semua spesifikasi</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-6 h-6 text-yellow-400" />
                      <div>
                        <p className="text-yellow-400 font-semibold">Sebagian Sesuai</p>
                        <p className="text-slate-400 text-sm">Beberapa batasan mungkin perlu disesuaikan</p>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              {/* Recommendation Cards */}
              <Card className="glass-card border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-cyan-400" />
                    Blend yang Direkomendasikan
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {recommendation.ai_recommendation.recommendation.map((coal, idx) => (
                      <div
                        key={idx}
                        className="p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-cyan-500/50 transition-all"
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h4 className="text-white font-semibold">{coal.supplier}</h4>
                            <p className="text-xs text-slate-400">{coal.source}</p>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            coal.type === 'MRC' 
                              ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                              : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          }`}>
                            {coal.type}
                          </span>
                        </div>
                        
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-400">Percentage:</span>
                            <span className="text-cyan-400 font-mono font-semibold">{coal.percentage}%</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-400">Tonnage:</span>
                            <span className="text-emerald-400 font-mono font-semibold">{coal.tonnage.toLocaleString()} MT</span>
                          </div>
                          
                          <div className="mt-3 pt-3 border-t border-slate-700 space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="text-slate-500">GCV:</span>
                              <span className="text-slate-300 font-mono">{coal.gcv} kcal/kg</span>
                            </div>
                            <div className="flex justify-between text-xs">
                              <span className="text-slate-500">Ash:</span>
                              <span className="text-slate-300 font-mono">{coal.ash}%</span>
                            </div>
                            <div className="flex justify-between text-xs">
                              <span className="text-slate-500">Sulphur:</span>
                              <span className="text-slate-300 font-mono">{coal.sulphur}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Quality Comparison - Radar Chart */}
              <Card className="glass-card border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Flame className="w-5 h-5 text-orange-400" />
                    Perbandingan Kualitas
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={radarChartData}>
                      <PolarGrid stroke="#334155" />
                      <PolarAngleAxis dataKey="metric" stroke="#94a3b8" />
                      <PolarRadiusAxis stroke="#334155" />
                      <Radar
                        name="Target"
                        dataKey="Target"
                        stroke="#22d3ee"
                        fill="#22d3ee"
                        fillOpacity={0.3}
                      />
                      <Radar
                        name="Predicted"
                        dataKey="Predicted"
                        stroke="#10b981"
                        fill="#10b981"
                        fillOpacity={0.5}
                      />
                      <Legend />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e293b',
                          border: '1px solid #334155',
                          borderRadius: '8px'
                        }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>

                  <div className="mt-4 grid grid-cols-3 gap-4">
                    <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">Prediksi GCV</p>
                      <p className="text-lg font-bold text-cyan-400">
                        {recommendation.ai_recommendation.predicted_quality.gcv}
                      </p>
                      <p className="text-xs text-slate-500">kcal/kg</p>
                    </div>
                    <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">Prediksi Abu</p>
                      <p className="text-lg font-bold text-yellow-400">
                        {recommendation.ai_recommendation.predicted_quality.ash}
                      </p>
                      <p className="text-xs text-slate-500">%</p>
                    </div>
                    <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">Prediksi Sulphur</p>
                      <p className="text-lg font-bold text-red-400">
                        {recommendation.ai_recommendation.predicted_quality.sulphur}
                      </p>
                      <p className="text-xs text-slate-500">%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* AI Reasoning */}
              <Card className="glass-card border-blue-500/30 bg-blue-500/5">
                <CardHeader className="pb-3">
                  <CardTitle className="text-white flex items-center gap-2 text-lg">
                    <Lightbulb className="w-5 h-5 text-yellow-400" />
                    Alasan AI
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm prose-invert max-w-none">
                    <ReactMarkdown
                      components={{
                        p: ({children}) => <p className="text-slate-300 leading-relaxed mb-3 text-sm">{children}</p>,
                        strong: ({children}) => <strong className="text-cyan-400 font-semibold">{children}</strong>,
                        ul: ({children}) => <ul className="list-disc list-inside space-y-1 text-slate-300 text-sm mb-3">{children}</ul>,
                        ol: ({children}) => <ol className="list-decimal list-inside space-y-1 text-slate-300 text-sm mb-3">{children}</ol>,
                        li: ({children}) => <li className="text-slate-300">{children}</li>,
                      }}
                    >
                      {recommendation.ai_recommendation.reasoning}
                    </ReactMarkdown>
                  </div>
                </CardContent>
              </Card>

              {/* Cost Warning */}
              {recommendation.ai_recommendation.cost_warning && (
                <Card className="glass-card border-orange-500/30 bg-orange-500/5">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-white flex items-center gap-2 text-lg">
                      <DollarSign className="w-5 h-5 text-orange-400" />
                      Analisis Biaya
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm prose-invert max-w-none">
                      <ReactMarkdown
                        components={{
                          p: ({children}) => <p className="text-orange-200 leading-relaxed mb-3 text-sm">{children}</p>,
                          strong: ({children}) => <strong className="text-orange-400 font-semibold">{children}</strong>,
                          ul: ({children}) => <ul className="list-disc list-inside space-y-1 text-orange-200 text-sm mb-3">{children}</ul>,
                          ol: ({children}) => <ol className="list-decimal list-inside space-y-1 text-orange-200 text-sm mb-3">{children}</ol>,
                          li: ({children}) => <li className="text-orange-200">{children}</li>,
                        }}
                      >
                        {recommendation.ai_recommendation.cost_warning}
                      </ReactMarkdown>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {recommendation?.ai_recommendation?.error && (
            <Card className="glass-card border-red-500/30 bg-red-500/5">
              <CardContent className="p-8 text-center">
                <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-red-400 mb-2">
                  Error Pemrosesan AI
                </h3>
                <p className="text-slate-400 text-sm">
                  {recommendation.ai_recommendation.error}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default SmartBlendingPage;
