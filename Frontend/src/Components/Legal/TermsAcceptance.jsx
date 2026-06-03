import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, CardBody, Col, Container, FormGroup, Input, Label, Row, Spinner } from "reactstrap";
import { toast } from "react-toastify";
import {
  acceptLegalAgreement,
  getCurrentLegalAgreement,
  getMyAgreementAcceptanceStatus,
} from "../../Services/Authentication";

const renderAgreementLine = (line, lineIndex) => {
  const headingText = line.replace(/^\s{0,3}#{1,6}\s*/, "");
  const isHeading = headingText !== line;
  const segments = headingText.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return (
    <div
      key={lineIndex}
      className={isHeading ? "fw-bold mt-3 mb-2" : ""}
      style={{ minHeight: line.trim() ? "auto" : "1.35em" }}
    >
      {segments.map((segment, segmentIndex) => {
        if (segment.startsWith("**") && segment.endsWith("**")) {
          return <strong key={segmentIndex}>{segment.slice(2, -2)}</strong>;
        }
        return <React.Fragment key={segmentIndex}>{segment}</React.Fragment>;
      })}
    </div>
  );
};

const AgreementContent = ({ content }) => {
  if (!content) {
    return <>Agreement content is not configured.</>;
  }
  return <>{content.split("\n").map(renderAgreementLine)}</>;
};

const TermsAcceptance = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [checked, setChecked] = useState(false);
  const [agreementData, setAgreementData] = useState(null);

  useEffect(() => {
    const loadAgreement = async () => {
      try {
        const status = await getMyAgreementAcceptanceStatus();
        if (status.accepted) {
          navigate("/dashboard/algoviewtech/user", { replace: true });
          return;
        }
        const data = await getCurrentLegalAgreement();
        setAgreementData(data);
      } catch (error) {
        toast.error(error?.response?.data?.detail || "Unable to load agreement.");
      } finally {
        setLoading(false);
      }
    };
    loadAgreement();
  }, [navigate]);

  const handleAccept = async () => {
    setSubmitting(true);
    try {
      await acceptLegalAgreement();
      toast.success("Agreement accepted successfully.");
      navigate("/dashboard/algoviewtech/user", { replace: true });
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Unable to accept agreement.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center min-vh-100">
        <Spinner color="primary" />
      </div>
    );
  }

  const agreement = agreementData?.agreement || {};
  const client = agreementData?.client || {};

  return (
    <div className="bg-light min-vh-100 py-4">
      <Container fluid="lg">
        <Row className="justify-content-center">
          <Col xl="10">
            <Card className="shadow-sm border-0">
              <CardBody className="p-4 p-md-5">
                <div className="mb-4">
                  <h3 className="mb-2">Software Development and Automation Services Agreement</h3>
                  <p className="text-muted mb-0">Please review and accept the current agreement to continue.</p>
                </div>

                <Row className="g-3 mb-4">
                  <Col md="4">
                    <Label className="fw-semibold">Name</Label>
                    <Input value={client.client_name || "-"} disabled />
                  </Col>
                  <Col md="4">
                    <Label className="fw-semibold">Mobile</Label>
                    <Input value={client.client_mobile || "-"} disabled />
                  </Col>
                  <Col md="4">
                    <Label className="fw-semibold">Email</Label>
                    <Input value={client.client_email || "-"} disabled />
                  </Col>
                  <Col md="6">
                    <Label className="fw-semibold">Agreement Title</Label>
                    <Input value={agreement.title || "-"} disabled />
                  </Col>
                  <Col md="2">
                    <Label className="fw-semibold">Version</Label>
                    <Input value={agreement.version || "-"} disabled />
                  </Col>
                  <Col md="4">
                    <Label className="fw-semibold">Terms Version Hash</Label>
                    <Input value={agreement.hash || "-"} disabled />
                  </Col>
                </Row>

                <div
                  className="border rounded bg-white p-3 mb-4"
                  style={{ maxHeight: "52vh", overflowY: "auto", lineHeight: 1.6 }}
                >
                  <AgreementContent content={agreement.content} />
                </div>

                <FormGroup check className="mb-4">
                  <Input id="legalAgreementCheck" type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)} />
                  <Label check htmlFor="legalAgreementCheck">
                    I have read and agree to the Software Development and Automation Services Agreement, Risk Disclaimer, Terms & Conditions and No Refund Policy.
                  </Label>
                </FormGroup>

                <Button color="primary" size="lg" disabled={!checked || submitting} onClick={handleAccept}>
                  {submitting ? <Spinner size="sm" className="me-2" /> : null}
                  ACCEPT & CONTINUE
                </Button>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default TermsAcceptance;
