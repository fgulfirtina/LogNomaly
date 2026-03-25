using Microsoft.AspNetCore.Identity;

namespace LogNomaly.Web.Utilities
{
    public static class PasswordHasher
    {
        // We use ASP.NET Core's built-in Identity PasswordHasher.
        // It uses PBKDF2 with HMAC-SHA256, a 128-bit salt, a 256-bit subkey, and 100,000 iterations.
        private static readonly PasswordHasher<object> _hasher = new PasswordHasher<object>();

        public static string HashPassword(string password)
        {
            // The 'null' object parameter is required by the API but not used for the actual hashing process.
            return _hasher.HashPassword(null!, password);
        }

        public static bool VerifyPassword(string hashedPassword, string providedPassword)
        {
            var result = _hasher.VerifyHashedPassword(null!, hashedPassword, providedPassword);
            return result == PasswordVerificationResult.Success;
        }
    }
}