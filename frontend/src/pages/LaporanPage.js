import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  FileText,
  Search,
  Download,
  Filter,
  Loader2,
  Ship,
  Anchor,
  Truck,
  Leaf,
  FileSpreadsheet,
  File,
  ShoppingCart,
  ListOrdered
} from "lucide-react";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import jsPDF from "jspdf";
import "jspdf-autotable";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const LaporanPage = () => {
  const { getAuthHeader } = useAuth();
  const [activeTab, setActiveTab] = useState("vessel");
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [data, setData] = useState([]);
  const [search, setSearch] = useState("");
  const [filterPeriode, setFilterPeriode] = useState("all");

  const categories = [
    { id: "vessel", label: "Vessel", icon: Ship, color: "cyan" },
    { id: "barge", label: "Barge", icon: Anchor, color: "blue" },
    { id: "trucking", label: "Trucking", icon: Truck, color: "amber" },
    { id: "biomassa", label: "Biomassa", icon: Leaf, color: "green" },
    { id: "po_batubara", label: "PO Batubara", icon: ShoppingCart, color: "purple" },
    { id: "merit_order", label: "Merit Order", icon: ListOrdered, color: "pink" }
  ];

  useEffect(() => {
    fetchData();
  }, [activeTab, search]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const endpoint = activeTab === "vessel" ? "vessels" : 
                       activeTab === "barge" ? "barges" : 
                       activeTab === "trucking" ? "trucking" : "biomassa";
      const params = search ? { search } : {};
      const response = await axios.get(`${API_URL}/api/${endpoint}`, { 
        headers: getAuthHeader(), 
        params 
      });
      setData(response.data);
    } catch (error) {
      toast.error("Gagal memuat data laporan");
    } finally {
      setLoading(false);
    }
  };

  const getTableColumns = () => {
    switch (activeTab) {
      case "vessel":
        return [
          { key: "periode_realisasi", label: "Periode" },
          { key: "shipment_code", label: "Shipment" },
          { key: "name_of_vessel", label: "Nama Vessel" },
          { key: "suppliers", label: "Supplier" },
          { key: "bl_mt", label: "B/L (MT)", type: "number" },
          { key: "ds_mt", label: "DS (MT)", type: "number" },
          { key: "gcv_arb", label: "GCV ARB", type: "number" }
        ];
      case "barge":
        return [
          { key: "periode", label: "Periode" },
          { key: "shipment_code", label: "Shipment" },
          { key: "suppliers", label: "Supplier" },
          { key: "tb", label: "TB" },
          { key: "bg", label: "BG" },
          { key: "bl_mt", label: "B/L (MT)", type: "number" },
          { key: "gcv_arb", label: "GCV ARB", type: "number" }
        ];
      case "trucking":
        return [
          { key: "periode_realisasi", label: "Periode" },
          { key: "shipment_code", label: "Shipment" },
          { key: "suppliers", label: "Supplier" },
          { key: "coal_from", label: "Lokasi" },
          { key: "ds_mt", label: "Total Tonase (MT)", type: "number" },
          { key: "gcv_arb", label: "GCV ARB", type: "number" }
        ];
      case "biomassa":
        return [
          { key: "periode", label: "Periode" },
          { key: "shipment_code", label: "Shipment" },
          { key: "suppliers", label: "Supplier" },
          { key: "coal_from", label: "Asal" },
          { key: "bl_mt", label: "B/L (MT)", type: "number" },
          { key: "gcv_arb", label: "GCV ARB", type: "number" }
        ];
      default:
        return [];
    }
  };

  const formatValue = (value, type) => {
    if (value === null || value === undefined) return "-";
    if (type === "number") return value.toLocaleString("id-ID");
    return value;
  };

  const formatDateForExport = (value) => {
    if (!value) return "-";
    try {
      const date = new Date(value);
      return date.toLocaleDateString("id-ID", { year: "numeric", month: "short", day: "numeric" });
    } catch {
      return value;
    }
  };

  const getTotalTonase = () => {
    const field = activeTab === "trucking" ? "ds_mt" : "bl_mt";
    return data.reduce((sum, item) => sum + (item[field] || 0), 0);
  };

  const getAvgGCV = () => {
    const validData = data.filter(item => item.gcv_arb);
    if (validData.length === 0) return 0;
    return validData.reduce((sum, item) => sum + item.gcv_arb, 0) / validData.length;
  };

  // Export to Excel
  const handleExportExcel = () => {
    if (data.length === 0) {
      toast.error("Tidak ada data untuk diekspor");
      return;
    }
    
    setExporting(true);
    try {
      const columns = getTableColumns();
      const currentCategory = categories.find(c => c.id === activeTab);
      
      // Prepare data for export
      const exportData = data.map((item, index) => {
        const row = { "No": index + 1 };
        columns.forEach(col => {
          let value = item[col.key];
          if (col.key.includes("periode") || col.key.includes("ta") || col.key.includes("time")) {
            value = formatDateForExport(value);
          } else if (col.type === "number" && value !== null && value !== undefined) {
            value = Number(value);
          }
          row[col.label] = value ?? "-";
        });
        return row;
      });

      // Add summary row
      exportData.push({});
      exportData.push({
        "No": "",
        [columns[0].label]: "TOTAL",
        [columns.find(c => c.type === "number")?.label || "Total"]: getTotalTonase(),
      });
      exportData.push({
        "No": "",
        [columns[0].label]: "Rata-rata GCV",
        [columns.find(c => c.key === "gcv_arb")?.label || "GCV"]: getAvgGCV().toFixed(2),
      });

      const ws = XLSX.utils.json_to_sheet(exportData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, currentCategory?.label || "Data");
      
      // Auto-size columns
      const colWidths = columns.map(col => ({ wch: Math.max(col.label.length + 2, 15) }));
      colWidths.unshift({ wch: 5 }); // No column
      ws["!cols"] = colWidths;

      const fileName = `Laporan_${currentCategory?.label}_${new Date().toISOString().split("T")[0]}.xlsx`;
      XLSX.writeFile(wb, fileName);
      toast.success(`Berhasil export ke ${fileName}`);
    } catch (error) {
      console.error("Export error:", error);
      toast.error("Gagal export ke Excel");
    } finally {
      setExporting(false);
    }
  };

  // Export to PDF
  const handleExportPDF = () => {
    if (data.length === 0) {
      toast.error("Tidak ada data untuk diekspor");
      return;
    }

    setExporting(true);
    try {
      const columns = getTableColumns();
      const currentCategory = categories.find(c => c.id === activeTab);
      
      const doc = new jsPDF("landscape", "mm", "a4");
      
      // Header
      doc.setFontSize(16);
      doc.setFont("helvetica", "bold");
      doc.text(`Laporan Data ${currentCategory?.label}`, 14, 15);
      
      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      doc.text(`PLTU Tenayan - Sistem Manajemen Bahan Bakar Digital`, 14, 22);
      doc.text(`Tanggal Export: ${new Date().toLocaleDateString("id-ID", { 
        weekday: "long", year: "numeric", month: "long", day: "numeric" 
      })}`, 14, 28);

      // Summary
      doc.setFontSize(10);
      doc.text(`Total Data: ${data.length} record`, 14, 36);
      doc.text(`Total Tonase: ${getTotalTonase().toLocaleString("id-ID")} MT`, 80, 36);
      doc.text(`Rata-rata GCV: ${getAvgGCV().toLocaleString("id-ID", { maximumFractionDigits: 2 })} Kcal/Kg`, 160, 36);

      // Table
      const tableColumns = ["No", ...columns.map(c => c.label)];
      const tableData = data.map((item, index) => {
        const row = [index + 1];
        columns.forEach(col => {
          let value = item[col.key];
          if (col.key.includes("periode") || col.key.includes("ta") || col.key.includes("time")) {
            value = formatDateForExport(value);
          } else if (col.type === "number" && value !== null && value !== undefined) {
            value = Number(value).toLocaleString("id-ID");
          }
          row.push(value ?? "-");
        });
        return row;
      });

      doc.autoTable({
        head: [tableColumns],
        body: tableData,
        startY: 42,
        styles: { fontSize: 8, cellPadding: 2 },
        headStyles: { fillColor: [30, 41, 59], textColor: 255 },
        alternateRowStyles: { fillColor: [241, 245, 249] },
        margin: { left: 14, right: 14 }
      });

      // Footer
      const pageCount = doc.internal.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.text(`Halaman ${i} dari ${pageCount}`, doc.internal.pageSize.width - 30, doc.internal.pageSize.height - 10);
      }

      const fileName = `Laporan_${currentCategory?.label}_${new Date().toISOString().split("T")[0]}.pdf`;
      doc.save(fileName);
      toast.success(`Berhasil export ke ${fileName}`);
    } catch (error) {
      console.error("PDF Export error:", error);
      toast.error("Gagal export ke PDF");
    } finally {
      setExporting(false);
    }
  };

  const columns = getTableColumns();
  const currentCategory = categories.find(c => c.id === activeTab);

  return (
    <div className="space-y-6" data-testid="laporan-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading font-bold text-2xl lg:text-3xl text-white flex items-center gap-3">
            <FileText className="w-8 h-8 text-purple-400" />
            Laporan Data
          </h1>
          <p className="text-slate-400 mt-1">Rekapitulasi data penerimaan bahan bakar</p>
        </div>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button 
              variant="outline" 
              className="border-slate-700 text-slate-300 hover:bg-slate-800" 
              data-testid="export-btn"
              disabled={exporting || data.length === 0}
            >
              {exporting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-2" />
              )}
              Export
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="bg-slate-900 border-slate-700">
            <DropdownMenuItem 
              onClick={handleExportExcel}
              className="text-slate-300 hover:bg-slate-800 cursor-pointer"
              data-testid="export-excel-btn"
            >
              <FileSpreadsheet className="w-4 h-4 mr-2 text-green-400" />
              Export ke Excel (.xlsx)
            </DropdownMenuItem>
            <DropdownMenuItem 
              onClick={handleExportPDF}
              className="text-slate-300 hover:bg-slate-800 cursor-pointer"
              data-testid="export-pdf-btn"
            >
              <File className="w-4 h-4 mr-2 text-red-400" />
              Export ke PDF
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass-card border-white/5 p-4">
          <p className="text-slate-400 text-sm">Total Data</p>
          <p className="text-2xl font-bold text-white mt-1">{data.length}</p>
          <p className="text-slate-500 text-xs mt-1">record {currentCategory?.label}</p>
        </Card>
        <Card className="glass-card border-white/5 p-4">
          <p className="text-slate-400 text-sm">Total Tonase</p>
          <p className="text-2xl font-bold text-cyan-400 mt-1">{getTotalTonase().toLocaleString("id-ID")}</p>
          <p className="text-slate-500 text-xs mt-1">MT (Metric Ton)</p>
        </Card>
        <Card className="glass-card border-white/5 p-4">
          <p className="text-slate-400 text-sm">Rata-rata GCV</p>
          <p className="text-2xl font-bold text-green-400 mt-1">{getAvgGCV().toLocaleString("id-ID", { maximumFractionDigits: 2 })}</p>
          <p className="text-slate-500 text-xs mt-1">Kcal/Kg (ARB)</p>
        </Card>
      </div>

      <Card className="glass-card border-white/5 p-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-slate-900/50 mb-4">
            {categories.map(cat => (
              <TabsTrigger 
                key={cat.id} 
                value={cat.id} 
                className={`text-xs data-[state=active]:bg-${cat.color}-500/20`}
                data-testid={`tab-${cat.id}`}
              >
                <cat.icon className="w-4 h-4 mr-2" />
                {cat.label}
              </TabsTrigger>
            ))}
          </TabsList>

          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <Input
                placeholder="Cari data..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 bg-slate-950/50 border-slate-800 text-white"
                data-testid="search-laporan-input"
              />
            </div>
            <Select value={filterPeriode} onValueChange={setFilterPeriode}>
              <SelectTrigger className="w-[180px] bg-slate-950/50 border-slate-800 text-white">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue placeholder="Filter Periode" />
              </SelectTrigger>
              <SelectContent className="bg-[#0B1221] border-slate-800">
                <SelectItem value="all" className="text-white">Semua Periode</SelectItem>
                <SelectItem value="2026" className="text-white">2026</SelectItem>
                <SelectItem value="2025" className="text-white">2025</SelectItem>
                <SelectItem value="2024" className="text-white">2024</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {categories.map(cat => (
            <TabsContent key={cat.id} value={cat.id}>
              <div className="rounded-lg border border-white/5 overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/5 hover:bg-transparent">
                      <TableHead className="text-slate-400 font-mono text-xs w-[50px]">No</TableHead>
                      {columns.map(col => (
                        <TableHead key={col.key} className="text-slate-400 font-mono text-xs">{col.label}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {loading ? (
                      <TableRow>
                        <TableCell colSpan={columns.length + 1} className="text-center py-8">
                          <Loader2 className="w-6 h-6 animate-spin text-purple-400 mx-auto" />
                        </TableCell>
                      </TableRow>
                    ) : data.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={columns.length + 1} className="text-center py-8 text-slate-500">
                          Tidak ada data ditemukan
                        </TableCell>
                      </TableRow>
                    ) : (
                      data.map((item, index) => (
                        <TableRow key={item.id} className="border-white/5 hover:bg-slate-900/50" data-testid={`laporan-row-${item.id}`}>
                          <TableCell className="text-slate-500 text-sm">{index + 1}</TableCell>
                          {columns.map(col => (
                            <TableCell key={col.key} className={`text-sm ${col.type === 'number' ? 'font-mono text-cyan-400' : 'text-slate-300'}`}>
                              {formatValue(item[col.key], col.type)}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </Card>
    </div>
  );
};

export default LaporanPage;
