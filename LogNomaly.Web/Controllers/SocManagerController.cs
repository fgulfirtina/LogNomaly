using LogNomaly.Web.Data;
using LogNomaly.Web.ViewModels;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace LogNomaly.Web.Controllers
{
    // Only Senior Analysts can access this entire controller
    [Authorize(Roles = "Senior")]
    public class SocManagerController : Controller
    {
        private readonly AppDbContext _context;

        public SocManagerController(AppDbContext context)
        {
            _context = context;
        }

        [HttpGet]
        public async Task<IActionResult> Index()
        {
            var viewModel = new SocManagerViewModel
            {
                // Fetch cases with their assigned analysts and the original feedback/log
                ActiveCases = await _context.InvestigationCases
                    .Include(c => c.AssignedAnalyst)
                    .Include(c => c.Feedback)
                    .OrderByDescending(c => c.OpenedAt)
                    .ToListAsync(),

                // Fetch only pending false positives that need model retraining approval
                PendingFalsePositives = await _context.AnalystFeedbacks
                    .Include(f => f.Analyst)
                    .Where(f => f.ActionType == "FalsePositive" && f.Status == "Pending")
                    .OrderByDescending(f => f.CreatedAt)
                    .ToListAsync()
            };

            return View(viewModel);
        }
    }
}