import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button, Badge, Modal, ModalHeader, ModalBody, ModalFooter } from 'reactstrap';
import { FaCheck, FaTimes, FaEye } from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { RotatingLines } from 'react-loader-spinner';
import "./KycUpdate.css";
import { baseUrl } from '../../../../../ConfigUrl/config';
import { fetchPeddingKycList, handleApprove, handleReject } from '../../../../../Services/Authentication';
import Swal from 'sweetalert2';
import { useNavigate } from 'react-router';

const KycList = () => {
  const [userData, setUserData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState([]);
  const [sortColumn, setSortColumn] = useState('id');
  const [error, setError] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [openModal, setOpenModal] = useState(false);
  const [rejectModal, setRejectModal] = useState(false);
  const [rejectDescription, setRejectDescription] = useState('');
  const [selectedKycId, setSelectedKycId] = useState(null);
  const navigate = useNavigate();
  const [proofImgesUrl, setProofImgesUrl] = useState('media/kyc_documents/front/dummyaadhar_EOs7a8p.png');
  const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
  const [isMobile, setIsMobile] = useState(false);
  const [pageBatch, setPageBatch] = useState(0);

  useEffect(() => {
    getUserData(searchQuery);

    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    return () => window.removeEventListener('resize', handleResize);

  }, [currentPage, itemsPerPage, searchQuery]);

  const pagesPerBatch = isMobile ? 2 : 4;

  const getUserData = async (query = '') => {
    try {
      setLoading(true);
      const data = await fetchPeddingKycList(currentPage, itemsPerPage, query);

      if (data.results && data.results.length > 0) {
        setUserData(data.results); // Directly store the paginated data.
        setTotalPages(Math.ceil(data.count / itemsPerPage));
      } else {
        setUserData([]); // Handle empty pages.
      }
    } catch (err) {
      console.error("Error fetching data:", err);
      setError("Failed to load data.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      setCurrentPage(1); // Reset to page 1 on new search
      getUserData(searchQuery);
    }
  };

  const handleSearchClick = () => {
    setCurrentPage(1);
    getUserData(searchQuery);
  };

  const onOpenModal = (fileUrl) => {
    setOpenModal(true);
    setProofImgesUrl(fileUrl)
  };
  const onCloseModal = () => {

    setOpenModal(false);

  };

  const handleSort = (users) => {
    const { key, direction } = sortConfig;
    if (!key) return users;

    return [...users].sort((a, b) => {
      if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
      if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const filteredUsers = Array.isArray(userData)
    ? userData.filter((user) => {
      const idProofName = user.id_proof
        ? {
          aadhar_card: 'Aadhar Card',
          pan_card: 'PAN Card',
          passport: 'Passport',
          voter_id: 'Voter Id',
          'driving-license': 'Driving License',
        }[user.id_proof.toLowerCase()] || ''
        : '';
      const addressProofName = user.address_proof_id
        ? {
          aadhar_card: 'Aadhar Card',
          pan_card: 'PAN Card',
          passport: 'Passport',
          voter_id: 'Voter Id',
          'driving-license': 'Driving License',
        }[user.address_proof_id.toLowerCase()] || ''
        : '';
      const dateTime = user.created_at || '';

      return (
        user.user_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        idProofName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        addressProofName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        dateTime.toLowerCase().includes(searchQuery.toLowerCase())
      );
    })
    : [];

  const indexOfLastUser = currentPage * itemsPerPage;
  const indexOfFirstUser = indexOfLastUser - itemsPerPage;

  let currentUsers = filteredUsers;

  if (currentPage === 1 && filteredUsers.length > itemsPerPage) {
    const extraItem = filteredUsers[filteredUsers.length - 1];
    currentUsers = [extraItem, ...currentUsers.slice(0, itemsPerPage - 1)];
  }

  const handleViewClick = (userId, docObj) => {
    navigate(`/kyc/kyclist/kycdetailview/:${userId}`, { state: docObj });
  };

  const handleApproveAction = async (kycId) => {
    const result = await Swal.fire({
      title: 'Are you sure want to approve ?',
      // text: 'You won\'t be able to revert this!',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText: 'Yes'
    });
    if (result.isConfirmed) {
      try {
        await handleApprove(kycId);
        setUserData(userData.map(user => user.id === kycId ? { ...user, status: 'approved' } : user));
        toast.success('KYC approved successfully!');
      } catch (error) {
        console.error('Error approving KYC:', error);
        toast.error('Failed to approve KYC.');
      }
    }
  };

  const handleRejectAction = (kycId) => {
    setSelectedKycId(kycId);
    setRejectModal(true);
  };

  const submitRejection = async () => {
    if (!rejectDescription.trim()) {
      toast.error('Description is required!');
      return;
    }

    try {
      await handleReject(selectedKycId, rejectDescription); // Pass reason here
      setUserData(userData.map(user => user.id === selectedKycId ? { ...user, status: 'rejected' } : user));
      toast.success('KYC rejected successfully!');
    } catch (error) {
      console.error('Error rejecting KYC:', error);
      toast.error('Failed to reject KYC.');
    } finally {
      closeRejectModal();
    }
  };

  const closeRejectModal = () => {
    setRejectModal(false);
    setRejectDescription('');
    setSelectedKycId(null);
  };

  const handlePreviousBatch = () => {
    if (pageBatch > 0) setPageBatch(pageBatch - 1);
  };

  const handleNextBatch = () => {
    const maxBatch = Math.ceil(totalPages / pagesPerBatch) - 1;
    if (pageBatch < maxBatch) setPageBatch(pageBatch + 1);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handlePrevious = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNext = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const startPage = pageBatch * pagesPerBatch + 1;
  const endPage = Math.min(startPage + pagesPerBatch - 1, totalPages);
  const pages = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);

  return (
    <Fragment>
      <Col sm="12">
        <Card style={{ marginTop: '80px' }}>
          <CardHeader>
            <div className="d-flex justify-content-between align-items-center custom-responsive-style">
              <div>
                <h3>KYC List</h3>
                {/* <span>{"Below is the list of KYC along with their details."}</span> */}
              </div>
              <div className='custom-responsive-style-search'>
                <Input
                  type="text"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                />
                <Button className='search-btn-clr' onClick={handleSearchClick}>Search</Button>

              </div>
            </div>
          </CardHeader>
          <div className="card-block row" style={{ height: '100%' }}>
            {!openModal && <Col sm="12" style={{ height: '100%' }}>
              {currentUsers.length === 0 ? (
                <div style={{ textAlign: 'left', paddingLeft: '25px', paddingTop: '15px' }}>
                  <p>{"No pending KYC requests"}</p>
                </div>
              ) : (
                <div className="table-responsive" style={{ height: '100%' }}>
                  <Table style={{ height: '100%' }}>
                    <thead>
                      <tr>
                        <th className='custom-col-design' onClick={() => handleSort('id')}>Sr no.</th>
                        <th className='custom-col-design' onClick={() => handleSort('user_name')}>User Name</th>
                        <th className='custom-col-design' onClick={() => handleSort('idProof')}>Name of ID Proof</th>
                        <th className='custom-col-design' onClick={() => handleSort('addressProofId')}>Name of Address Proof</th>
                        <th className='custom-col-design' onClick={() => handleSort('idProof')}>Id proof</th>
                        <th className='custom-col-design' onClick={() => handleSort('AddressProof')}>Address proof</th>
                        <th className='custom-col-design' onClick={() => handleSort('status')}>Status</th>
                        <th className='custom-col-design' onClick={() => handleSort('created_at')}>Date/Time</th>
                        <th className='custom-col-design' >Actions</th>
                        <th className='custom-col-design'>View</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loading ? (
                        <tr>
                          <td colSpan="9" style={{ textAlign: 'center', height: '100px' }}>
                            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                              <RotatingLines
                                strokeColor="#283F7B"
                                strokeWidth="4"
                                animationDuration="0.75"
                                width="50"
                                visible={true}
                              />
                            </div>
                          </td>
                        </tr>
                      ) : currentUsers.map((user, index) => (
                        <tr key={user.id}>
                          <td>{indexOfFirstUser + index + 1}</td>
                          <td>{user.user_name}</td>
                          {/* Name of ID Proof Column */}
                          <td>
                            {user.id_proof === 'aadhar_card' ? 'Aadhar Card' :
                              user.id_proof === 'pan_card' ? 'PAN Card' :
                                user.id_proof === 'passport' ? 'Passport' :
                                  user.id_proof === 'voter_id' ? 'Voter Id' :
                                    user.id_proof === 'driving-license' ? 'Driving License' : ''}
                          </td>
                          {/* Name of Address Proof Column */}
                          <td>
                            {user.address_proof_id === 'aadhar_card' ? 'Aadhar Card' :
                              user.address_proof_id === 'pan_card' ? 'PAN Card' :
                                user.address_proof_id === 'passport' ? 'Passport' :
                                  user.address_proof_id === 'voter_id' ? 'Voter Id' :
                                    user.address_proof_id === 'driving-license' ? 'Driving License' : ''}
                          </td>
                          <td>
                            <img className='img-fluid b-r-5 me-3 img-40 image-custom-style image-custom-responsive' onClick={() => onOpenModal(user.document_file_front)} src={`${baseUrl}/${user.document_file_front}`} alt='' />
                            <img className='img-fluid b-r-5 me-3 img-40 image-custom-style image-custom-responsive' onClick={() => onOpenModal(user.document_file_back)} src={`${baseUrl}/${user.document_file_back}`} alt='' />
                          </td>
                          <td>
                            <img className='img-fluid b-r-5 me-3 img-40 image-custom-style image-custom-responsive' onClick={() => onOpenModal(user.address_prof_front)} src={`${baseUrl}/${user.address_prof_front}`} alt='' />
                            <img className='img-fluid b-r-5 me-3 img-40 image-custom-style image-custom-responsive' onClick={() => onOpenModal(user.address_prof_back)} src={`${baseUrl}/${user.address_prof_back}`} alt='' />
                          </td>
                          <td>
                            {user.status === 'approved' ? (
                              <Badge pill className="status-pill" style={{ padding: '8px', border: '1px solid green', color: 'green', backgroundColor: 'transparent' }}>
                                Approved
                              </Badge>
                            ) : user.status === 'rejected' ? (
                              <Badge pill className="status-pill" style={{ padding: '8px', border: '1px solid red', color: 'red', backgroundColor: 'transparent' }}>
                                Rejected
                              </Badge>
                            ) : user.status === 'pending' ? (
                              <Badge pill className="status-pill" style={{ padding: '8px', border: '1px solid blue', color: 'blue', backgroundColor: 'transparent' }}>
                                Pending
                              </Badge>
                            ) : null}
                          </td>
                          <td>{new Date(user.created_at).toLocaleString()}</td>
                          <td>
                            {user.status === 'approved' ? (
                              <FaCheck style={{ color: 'green', fontSize: '20px', margin: '0 10px' }} />
                            ) : user.status === 'rejected' ? (
                              <FaTimes style={{ color: 'red', fontSize: '20px', margin: '0 10px' }} />
                            ) : user.status === 'pending' ? (
                              <>
                                <Button color="success" onClick={() => handleApproveAction(user.id)} className='custom-btn-style custom-btn-responsive'>
                                  <FaCheck style={{ marginRight: '5px' }} /> Approve
                                </Button>
                                <Button color="danger" onClick={() => handleRejectAction(user.id)} className='custom-btn-styles'>
                                  <FaTimes style={{ marginRight: '5px' }} /> Reject
                                </Button>
                              </>
                            ) : null}
                          </td>

                          <td>
                            <FaEye className="view-icon" onClick={() => handleViewClick(user.id, {
                              id: user.id,
                              document_file_front: `${user.document_file_front}`,
                              document_file_back: `${user.document_file_back}`,
                              address_prof_front: `${user.address_prof_front}`,
                              address_prof_back: `${user.address_prof_back}`,
                            })} style={{ cursor: 'pointer', fontSize: '18px' }} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>

                </div>
              )}
              <div className={`d-flex justify-content-end align-items-center ${isMobile ? 'gap-0' : 'gap-0'} custom-pagi-style`}>
                <p className="mb-0 me-2">Rows per page</p>
                <Input
                  type="select"
                  value={itemsPerPage}
                  onChange={(e) => {
                    setItemsPerPage(parseInt(e.target.value));
                    setCurrentPage(1); // Reset to page 1 when changing items per page
                  }}
                  style={{ width: '80px' }}
                  className="me-3"
                >
                  <option value="10">10</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                </Input>

                <Pagination>
                  {/* Previous button */}
                  <PaginationItem disabled={currentPage === 1}>
                    <PaginationLink previous onClick={handlePrevious}>
                      {isMobile ? 'Pre' : 'Previous'}
                    </PaginationLink>
                  </PaginationItem>

                  {/* '<' arrow */}
                  {pageBatch > 0 && (
                    <PaginationItem>
                      <PaginationLink onClick={handlePreviousBatch}>&lt;</PaginationLink>
                    </PaginationItem>
                  )}

                  {/* Page numbers */}
                  {pages.map((page) => (
                    <PaginationItem active={page === currentPage} key={page}>
                      <PaginationLink onClick={() => handlePageChange(page)}>{page}</PaginationLink>
                    </PaginationItem>
                  ))}

                  {/* '>' arrow */}
                  {endPage < totalPages && (
                    <PaginationItem>
                      <PaginationLink onClick={handleNextBatch}>&gt;</PaginationLink>
                    </PaginationItem>
                  )}

                  {/* Next button */}
                  <PaginationItem disabled={currentPage === totalPages}>
                    <PaginationLink next onClick={handleNext}>
                      Next
                    </PaginationLink>
                  </PaginationItem>
                </Pagination>
              </div>
            </Col>}
            {openModal && <Col sm="12" style={{ height: '100%' }}>
              <Button onClick={() => onCloseModal()} color="primary search-btn-clr" style={{ alignItems: 'center', margin: '10px' }}>Back</Button>
              <div className="d-flex justify-content-between align-items-center">
                <div className="d-flex " style={{ justifyContent: 'center', width: '100%' }}>
                  <img style={{ maxHeight: '700px', maxWidth: '700px', margin: '30px' }} className='img-fluid b-r-5 me-3 ' src={`${baseUrl}/${proofImgesUrl}`} alt='' />
                </div>
              </div>
            </Col>}
          </div>
        </Card>
      </Col>

      {/* Reject Modal */}
      <Modal isOpen={rejectModal} toggle={closeRejectModal}>
        <ModalHeader toggle={closeRejectModal}>Reject KYC</ModalHeader>
        <ModalBody>
          <Input
            type="textarea"
            placeholder="Enter rejection reason..."
            value={rejectDescription}
            onChange={(e) => setRejectDescription(e.target.value)}
          />
        </ModalBody>
        <ModalFooter>
          <Button className="search-btn-clr" onClick={submitRejection}>Submit</Button>
          <Button color="danger" style={{ marginLeft: '10px' }} onClick={closeRejectModal}>Cancel</Button>
        </ModalFooter>
      </Modal>


      {/* Toast Container */}
      <ToastContainer position="top-right" autoClose={3000} hideProgressBar={false} newestOnTop={false} closeOnClick rtl={false} pauseOnFocusLoss draggable pauseOnHover />
    </Fragment>
  );
};

export default KycList;