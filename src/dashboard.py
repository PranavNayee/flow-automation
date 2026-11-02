"""
Streamlit dashboard for monitoring and controlling the automation
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.queue_manager import QueueManager, JobStatus
from src.credit_tracker import CreditTracker
from src.utils import Config, RateLimiter


def load_data():
    """Load data from database and trackers."""
    config = Config()
    queue_manager = QueueManager()
    credit_tracker = CreditTracker(
        monthly_limit=config.get_env('MONTHLY_CREDIT_LIMIT', None)
    )
    
    max_per_hour = config.get_env('MAX_GENERATIONS_PER_HOUR', 10)
    max_per_day = config.get_env('MAX_GENERATIONS_PER_DAY', 50)
    rate_limiter = RateLimiter(max_per_hour, max_per_day)
    
    return queue_manager, credit_tracker, rate_limiter


def main():
    """Main dashboard function."""
    st.set_page_config(
        page_title="Flow Automation Dashboard",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Flow Automation Dashboard")
    st.markdown("---")
    
    # Load data
    queue_manager, credit_tracker, rate_limiter = load_data()
    
    # Sidebar - Stats
    with st.sidebar:
        st.header("📊 Statistics")
        
        # Queue stats
        stats = queue_manager.get_stats()
        st.metric("Total Jobs", stats['total'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Pending", stats['pending'])
            st.metric("Running", stats['running'])
        with col2:
            st.metric("Completed", stats['completed'])
            st.metric("Failed", stats['failed'])
        
        st.markdown("---")
        
        # Credit usage
        st.header("💳 Credits")
        credit_usage = credit_tracker.get_usage()
        
        if 'monthly_limit' in credit_usage:
            progress = credit_usage['monthly_usage'] / credit_usage['monthly_limit']
            st.progress(progress)
            st.metric(
                "Monthly Usage",
                f"{credit_usage['monthly_usage']} / {credit_usage['monthly_limit']}"
            )
            st.metric("Remaining", credit_usage['remaining'])
        else:
            st.metric("Total Usage", credit_usage['total_usage'])
        
        st.markdown("---")
        
        # Rate limiter
        st.header("⏱️ Rate Limits")
        rate_stats = rate_limiter.get_stats()
        
        st.metric(
            "Hourly",
            f"{rate_stats['hourly']['used']} / {rate_stats['hourly']['limit']}"
        )
        st.metric(
            "Daily",
            f"{rate_stats['daily']['used']} / {rate_stats['daily']['limit']}"
        )
    
    # Main content - Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Queue", 
        "✅ Completed", 
        "❌ Failed",
        "🎬 Preview & Review"
    ])
    
    # Tab 1: Queue
    with tab1:
        st.header("Job Queue")
        
        pending_jobs = queue_manager.get_all_jobs(status=JobStatus.PENDING.value)
        running_jobs = queue_manager.get_all_jobs(status=JobStatus.RUNNING.value)
        
        if running_jobs:
            st.subheader("🔄 Running")
            for job in running_jobs:
                with st.expander(f"🔄 {job.scene_id} - Running"):
                    st.write(f"**Prompt:** {job.prompt}")
                    st.write(f"**Aspect Ratio:** {job.aspect_ratio}")
                    st.write(f"**Started:** {job.started_at}")
        
        if pending_jobs:
            st.subheader("⏳ Pending")
            
            df = pd.DataFrame([
                {
                    'Scene ID': job.scene_id,
                    'Prompt': job.prompt[:100] + '...' if len(job.prompt) > 100 else job.prompt,
                    'Aspect Ratio': job.aspect_ratio,
                    'Created': job.created_at
                }
                for job in pending_jobs
            ])
            
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No pending jobs")
    
    # Tab 2: Completed
    with tab2:
        st.header("Completed Jobs")
        
        completed_jobs = queue_manager.get_all_jobs(
            status=JobStatus.COMPLETED.value,
            limit=50
        )
        
        if completed_jobs:
            for job in completed_jobs:
                with st.expander(f"✅ {job.scene_id}"):
                    st.write(f"**Prompt:** {job.prompt}")
                    st.write(f"**Completed:** {job.completed_at}")
                    
                    if job.output_path and Path(job.output_path).exists():
                        st.write(f"**File:** {job.output_path}")
                        
                        # Show video if it exists
                        try:
                            st.video(job.output_path)
                        except:
                            st.warning("Could not display video")
        else:
            st.info("No completed jobs yet")
    
    # Tab 3: Failed
    with tab3:
        st.header("Failed Jobs")
        
        failed_jobs = queue_manager.get_all_jobs(
            status=JobStatus.FAILED.value,
            limit=50
        )
        
        if failed_jobs:
            for job in failed_jobs:
                with st.expander(f"❌ {job.scene_id}", expanded=False):
                    st.write(f"**Prompt:** {job.prompt}")
                    st.error(f"**Error:** {job.error_message}")
                    st.write(f"**Retry Count:** {job.retry_count}")
                    st.write(f"**Failed:** {job.completed_at}")
                    
                    # Retry button
                    if st.button(f"Retry {job.scene_id}", key=f"retry_{job.id}"):
                        queue_manager.update_job(
                            job.id,
                            status=JobStatus.RETRY.value,
                            error_message=None
                        )
                        st.success("Job marked for retry")
                        st.rerun()
        else:
            st.success("No failed jobs")
    
    # Tab 4: Preview & Review
    with tab4:
        st.header("Preview & Review")
        st.info("Coming soon: Preview completed videos and approve/reject for upload")
        
        completed_jobs = queue_manager.get_all_jobs(
            status=JobStatus.COMPLETED.value,
            limit=10
        )
        
        if completed_jobs:
            for job in completed_jobs:
                if job.output_path and Path(job.output_path).exists():
                    st.subheader(job.scene_id)
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        try:
                            st.video(job.output_path)
                        except:
                            st.error("Could not load video")
                    
                    with col2:
                        st.write(f"**Prompt:** {job.prompt}")
                        st.write(f"**File:** {Path(job.output_path).name}")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅ Approve", key=f"approve_{job.id}"):
                                st.success("Approved for upload")
                        with col_b:
                            if st.button("❌ Reject", key=f"reject_{job.id}"):
                                st.warning("Marked for deletion")
                    
                    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()


if __name__ == "__main__":
    main()
