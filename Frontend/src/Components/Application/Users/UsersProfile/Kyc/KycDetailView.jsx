import React, { useEffect, useState } from 'react';
import { Container, Row, Col, Card, CardBody, Form, FormGroup, Label, Input, Button } from 'reactstrap';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { baseUrl } from '../../../../../ConfigUrl/config';
import '../UserProfiles.css';
import { getKycViewById } from '../../../../../Services/Authentication';

const KycDetailView = () => {
  const [userProfile, setUserProfile] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    userName: '',
    status: '',
    createdAt: '',
  });
  const [kycData, setKycData] = useState({});
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = location.state || {};

  useEffect(() => {
    fetchKycData();
  }, [id]);

  const fetchKycData = async () => {
    try {
      const response = await getKycViewById(id);

      // Format the created_at date
      const formattedDate = new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }).format(new Date(response.created_at));

      setKycData(response);
      setUserProfile({
        firstName: response.first_name || '',
        lastName: response.last_name || '',
        email: response.email || '',
        phone: response.phone || '',
        userName: response.user_name || '',
        status: response.status || '',
        createdAt: formattedDate,
      });
    } catch (error) {
      toast.error('Failed to load KYC details');
    }
  };

  const placeholderImg = 'https://via.placeholder.com/150';

  const renderImage = (imgSrc, altText) => (
    <div className="image-container text-center">
      <img
        style={{ cursor: 'pointer' }}
        className="img-fluid b-r-5 me-3 img-150"
        src={imgSrc ? `${baseUrl}/${imgSrc}` : placeholderImg}
        alt={altText}
      />
      {!imgSrc && <p style={{ color: 'gray', marginTop: '10px' }}>No Img Found</p>}
    </div>
  );

  const { document_file_front, document_file_back, address_prof_front, address_prof_back } = kycData;

  return (
    <Container fluid>
      <ToastContainer />
      <Row className="justify-content-center">
        <Col md="10" style={{ width: '100%' }}>
          <Card style={{marginTop: '30px'}}>
            <CardBody>
              <Row style={{ minHeight: '400px' }}>
                {/* About Me Section */}
                <Col md="6" className="border-right">
                  <h4 className="mt-4 mb-5 text-center">About Me</h4>
                  <Form className="theme-form mt-3">
                    <FormGroup className="row">
                      <Label className="col-sm-4 col-form-label">Full Name</Label>
                      <Col sm="8">
                        <Input style={{lineHeight: '2'}} type="text" value={userProfile.userName} readOnly placeholder="Full Name" />
                      </Col>
                    </FormGroup>
                    <FormGroup className="row">
                      <Label className="col-sm-4 col-form-label">First Name</Label>
                      <Col sm="8">
                        <Input style={{lineHeight: '2'}} type="text" value={userProfile.firstName} readOnly placeholder="First Name" />
                      </Col>
                    </FormGroup>
                    <FormGroup className="row">
                      <Label className="col-sm-4 col-form-label">Last Name</Label>
                      <Col sm="8">
                        <Input style={{lineHeight: '2'}} type="text" value={userProfile.lastName} readOnly placeholder="Last Name" />
                      </Col>
                    </FormGroup>
                    <FormGroup className="row">
                      <Label className="col-sm-4 col-form-label">Email</Label>
                      <Col sm="8">
                        <Input style={{lineHeight: '2'}} type="email" value={userProfile.email} readOnly placeholder="Email" />
                      </Col>
                    </FormGroup>
                    <FormGroup className="row">
                      <Label className="col-sm-4 col-form-label">Phone</Label>
                      <Col sm="8">
                        <Input style={{lineHeight: '2'}} type="text" value={userProfile.phone} readOnly placeholder="Phone" />
                      </Col>
                    </FormGroup>
                    <FormGroup className="row">
                      <Label className="col-sm-4 col-form-label">Date/Time</Label>
                      <Col sm="8">
                        <Input  style={{lineHeight: '2'}} type="text" value={userProfile.createdAt} readOnly placeholder="Date/Time" />
                      </Col>
                    </FormGroup>
                    <FormGroup className="row">
                      <Label className="col-sm-4 col-form-label">Status</Label>
                      <Col sm="8">
                        <Input style={{lineHeight: '2'}} type="text" value={userProfile.status} readOnly placeholder="Status" />
                      </Col>
                    </FormGroup>
                  </Form>
                </Col>

                {/* View Documents Section */}
                <Col md="6">
                  <h4 className="mt-4 mb-5 text-center">View Documents</h4>
                  <div className="mt-4">
                    <h6 style={{ marginBottom: '20px' }}>Address Proof</h6>
                    <Row>
                      <Col lg="6">{renderImage(address_prof_back, 'Address Proof Back')}</Col>
                      <Col lg="6">{renderImage(address_prof_front, 'Address Proof Front')}</Col>
                    </Row>

                    <h6 style={{ marginTop: '20px', marginBottom: '20px' }}>ID Proof</h6>
                    <Row>
                      <Col lg="6">{renderImage(document_file_front, 'Document Proof Front')}</Col>
                      <Col lg="6">{renderImage(document_file_back, 'Document Proof Back')}</Col>
                    </Row>
                  </div>
                </Col>
              </Row>
              {/* Common Back Button */}
              <Row className="justify-content-center mt-4">
                <Col sm="auto">
                  <Button
                    className="btn btn-primary search-btn-clr"
                    onClick={() => navigate('/kyc/kyclist')}
                  >
                    Back
                  </Button>
                </Col>
              </Row>
            </CardBody>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default KycDetailView;
