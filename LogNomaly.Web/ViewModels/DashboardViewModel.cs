using LogNomaly.Web.Entities.Models;

namespace LogNomaly.Web.ViewModels
{
    public class DashboardViewModel
    {
        public AnalysisStats? Stats { get; set; }
        public List<AnalysisResult> RecentResults { get; set; } = new();
        public string? SessionId { get; set; }
        public bool HasData => Stats != null && Stats.TotalLogs > 0;
    }
}
