# Publisher Service Tasks

## Current Status
- **Date**: 2025-09-10
- **Service**: Publisher (Lighttpd + CGI)
- **Version**: v2.0.3

## Completed Tasks
1. ✅ **Check publisher pod status**
   - Pod is running successfully
   - Lighttpd server started (lighttpd/1.4.79)

2. ✅ **Test publisher web interface via port forwarding**
   - Port forwarding established on localhost:8888
   - Web interface is accessible

3. ✅ **Fix database schema error in publisher CGI scripts**
   - Updated `index.py` to use `outlet_name` instead of `outlet`
   - Fixed column reference in SQL query (line 26)

## In Progress
4. 🔄 **Rebuild and deploy publisher with fixed CGI scripts**
   - Built Docker image v2.0.3 with `--no-cache`
   - Updated deployment manifest to use v2.0.3
   - Deployment restarted but container still shows old code
   - **Issue**: Docker build cache may be preventing updates from being included

## Pending Tasks
5. ⏳ **Clean up duplicate deployment structure**
   - **Problem**: Two deployment structures exist:
     - Old: `/deployment/publisher/` 
     - New: `/services/publisher/k8s/` (semver structure)
   - **Action Required**: 
     - Remove old deployment directory
     - Consolidate all manifests in services directory
     - Update any references to old paths

## Known Issues
1. **Database Schema Mismatch**
   - CGI scripts still reference old `outlet` column
   - Should use `outlet_name` as per database schema standardization

2. **Docker Build Cache**
   - Despite using `--no-cache`, container still has old code
   - May need to use different image tag or force pull

3. **Deployment Structure Confusion**
   - Two different deployment locations causing confusion
   - Services directory should be the canonical location for semver deployments

## Next Steps
1. Verify Docker image actually contains updated code
2. Force deployment to use new image (possibly with different tag)
3. Clean up old deployment directory structure
4. Test that web interface displays articles correctly
5. Verify all CGI scripts use correct database schema

## Architecture Notes
- Publisher uses Alpine Linux base image
- Lighttpd serves static content and CGI scripts
- Python CGI scripts connect directly to PostgreSQL
- ConfigMap provides lighttpd configuration
- Service runs on port 8080 internally

## Database Schema Reference
- Table: `articles`
- Correct column: `outlet_name` (NOT `outlet`)
- Other columns: `url`, `title`, `published_at`, `text`