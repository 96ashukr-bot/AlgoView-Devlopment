import React, { useEffect, useState } from "react";
import { Button, Card, CardBody, CardHeader, Col, Input, Modal, ModalBody, ModalHeader, Row, Spinner, Table } from "reactstrap";
import { toast } from "react-toastify";
import {
  downloadLegalAcceptancePdf,
  getLegalAcceptances,
  resendLegalAcceptanceEmail,
} from "../../Services/Authentication";

const formatDateTime = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-IN", { hour12: false });
};

const saveBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
};

const AgreementAcceptanceManagement = () => {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [pageNumber, setPageNumber] = useState(1);
  const [count, setCount] = useState(0);
  const [busyId, setBusyId] = useState(null);
  const [selectedAcceptance, setSelectedAcceptance] = useState(null);

  const fetchRows = async (nextPage = pageNumber) => {
    setLoading(true);
    try {
      const response = await getLegalAcceptances({ page_number: nextPage, page_size: 100, search });
      setRows(response.results || []);
      setCount(response.count || 0);
      setPageNumber(nextPage);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Unable to load agreement acceptances.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRows(1);
  }, []);

  const handleDownload = async (row) => {
    setBusyId(row.id);
    try {
      const blob = await downloadLegalAcceptancePdf(row.id);
      saveBlob(blob, `agreement-${row.client_name || row.client_id}-${row.agreement_version}.pdf`);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Unable to download PDF.");
    } finally {
      setBusyId(null);
    }
  };

  const handleResend = async (row, target) => {
    setBusyId(row.id);
    try {
      await resendLegalAcceptanceEmail(row.id, target);
      toast.success("Email resend request completed.");
      fetchRows(pageNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Unable to resend email.");
    } finally {
      setBusyId(null);
    }
  };

  const totalPages = Math.max(1, Math.ceil(count / 100));

  return (
    <Card>
      <CardHeader>
        <Row className="align-items-center g-2">
          <Col md="6">
            <h5 className="mb-0">Agreement Acceptance Management</h5>
          </Col>
          <Col md="4">
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search client name or email"
            />
          </Col>
          <Col md="2" className="text-md-end">
            <Button color="primary" onClick={() => fetchRows(1)}>Search</Button>
          </Col>
        </Row>
      </CardHeader>
      <CardBody>
        <div className="table-responsive">
          <Table hover className="align-middle">
            <thead>
              <tr>
                <th>Client Name</th>
                <th>Mobile</th>
                <th>Email</th>
                <th>Agreement Version</th>
                <th>Accepted Date</th>
                <th>IP Address</th>
                <th>Email Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" className="text-center py-4"><Spinner size="sm" /></td>
                </tr>
              ) : rows.length ? (
                rows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.client_name || "-"}</td>
                    <td>{row.client_mobile || "-"}</td>
                    <td>{row.client_email || "-"}</td>
                    <td>{row.agreement_version || "-"}</td>
                    <td>{formatDateTime(row.accepted_at)}</td>
                    <td>{row.ip_address || "-"}</td>
                    <td>{row.email_status || "-"}</td>
                    <td>
                      <div className="d-flex flex-wrap gap-2">
                        <Button size="sm" color="primary" disabled={busyId === row.id} onClick={() => handleDownload(row)}>Download PDF</Button>
                        <Button size="sm" color="info" disabled={busyId === row.id} onClick={() => setSelectedAcceptance(row)}>View</Button>
                        <Button size="sm" color="secondary" disabled={busyId === row.id} onClick={() => handleResend(row, "client")}>Resend Client</Button>
                        <Button size="sm" color="secondary" disabled={busyId === row.id} onClick={() => handleResend(row, "admin")}>Resend Admin</Button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" className="text-center py-4">No acceptances found.</td>
                </tr>
              )}
            </tbody>
          </Table>
        </div>

        <div className="d-flex justify-content-between align-items-center mt-3">
          <span>Page {pageNumber} of {totalPages}</span>
          <div className="d-flex gap-2">
            <Button disabled={pageNumber <= 1 || loading} onClick={() => fetchRows(pageNumber - 1)}>Previous</Button>
            <Button disabled={pageNumber >= totalPages || loading} onClick={() => fetchRows(pageNumber + 1)}>Next</Button>
          </div>
        </div>

        <Modal isOpen={Boolean(selectedAcceptance)} toggle={() => setSelectedAcceptance(null)} size="lg">
          <ModalHeader toggle={() => setSelectedAcceptance(null)}>Acceptance Details</ModalHeader>
          <ModalBody>
            {selectedAcceptance ? (
              <Table bordered responsive>
                <tbody>
                  <tr><th>Client Name</th><td>{selectedAcceptance.client_name || "-"}</td></tr>
                  <tr><th>Email</th><td>{selectedAcceptance.client_email || "-"}</td></tr>
                  <tr><th>Mobile</th><td>{selectedAcceptance.client_mobile || "-"}</td></tr>
                  <tr><th>Agreement Version</th><td>{selectedAcceptance.agreement_version || "-"}</td></tr>
                  <tr><th>Terms Hash</th><td style={{ wordBreak: "break-all" }}>{selectedAcceptance.terms_version_hash || "-"}</td></tr>
                  <tr><th>Accepted Date</th><td>{formatDateTime(selectedAcceptance.accepted_at)}</td></tr>
                  <tr><th>IP Address</th><td>{selectedAcceptance.ip_address || "-"}</td></tr>
                  <tr><th>User Agent</th><td style={{ wordBreak: "break-word" }}>{selectedAcceptance.user_agent || "-"}</td></tr>
                  <tr><th>Email Status</th><td>{selectedAcceptance.email_status || "-"}</td></tr>
                </tbody>
              </Table>
            ) : null}
          </ModalBody>
        </Modal>
      </CardBody>
    </Card>
  );
};

export default AgreementAcceptanceManagement;
