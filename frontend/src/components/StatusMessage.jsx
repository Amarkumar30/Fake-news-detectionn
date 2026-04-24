function StatusMessage({ type = "info", message, action, isLoading = false }) {
  if (!message) {
    return null;
  }

  return (
    <div className={`status-banner status-${type}`}>
      <div className="status-copy">
        {isLoading ? <span className="button-spinner status-spinner" aria-hidden="true" /> : null}
        <p>{message}</p>
      </div>
      {action}
    </div>
  );
}

export default StatusMessage;
