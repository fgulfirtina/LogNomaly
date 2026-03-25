namespace LogNomaly.Web.Entities.Models
{
    public class HealthResponse
    {
        public string Status { get; set; } = "";
        public bool ModelsLoaded { get; set; }
        public string Version { get; set; } = "";
        public int NFeatures { get; set; }
    }
}
