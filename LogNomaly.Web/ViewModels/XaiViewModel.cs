using LogNomaly.Web.Entities.Models;

namespace LogNomaly.Web.ViewModels
{
    public class XaiViewModel
    {
        public AnalysisResult? Result { get; set; }
        public string? SessionId { get; set; }
    }
}
