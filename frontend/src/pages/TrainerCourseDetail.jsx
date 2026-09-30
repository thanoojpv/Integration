import React, {
  useEffect,
  useState
} from 'react'

import {
  Link,
  useParams
} from 'react-router-dom'

import DashboardLayout
  from '../components/DashboardLayout'

import {
  apiRequest,
  fetchAuthenticatedBlob
} from '../services/api'
import { useNotification } from '../context/NotificationContext'


export default function TrainerCourseDetail() {

  const { courseId } = useParams()
  const { showNotification } = useNotification()


  // =====================================================
  // COURSE STATE
  // =====================================================

  const [courseData, setCourseData] =
    useState(null)

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState('')


  // =====================================================
  // EDIT COURSE STATE
  // =====================================================

  const [editingCourse, setEditingCourse] =
    useState(false)

  const [courseTitle, setCourseTitle] =
    useState('')

  const [courseLevel, setCourseLevel] =
    useState('Beginner')

  const [courseDescription, setCourseDescription] =
    useState('')

  const [savingCourse, setSavingCourse] =
    useState(false)

      // =====================================================
  // EDIT MODULE STATE
  // =====================================================

  const [editingModule, setEditingModule] =
    useState(null)

  const [moduleTitle, setModuleTitle] =
    useState('')

  const [savingModule, setSavingModule] =
    useState(null)


  // =====================================================
  // UPLOAD STATE
  // =====================================================

  const [uploadingVideo, setUploadingVideo] =
    useState(null)

  const [uploadingPdf, setUploadingPdf] =
    useState(null)


  // =====================================================
  // DURATION STATE
  // =====================================================

  const [durationValues, setDurationValues] =
    useState({})

  const [savingDuration, setSavingDuration] =
    useState(null)


  // =====================================================
  // VIEW STATE
  // =====================================================

  const [openingResource, setOpeningResource] =
    useState(null)


  // =====================================================
  // DELETE STATE
  // =====================================================

  const [deletingResource, setDeletingResource] =
    useState(null)



  // =====================================================
  // LOAD COURSE
  // =====================================================

  async function loadCourse() {

    try {

      setLoading(true)

      setError('')


      const data =
        await apiRequest(
          `/api/courses/${courseId}`
        )


      console.log(
        'TRAINER COURSE:',
        data
      )


      setCourseData(data)


      // -------------------------------------------------
      // Store current duration values
      // -------------------------------------------------

      const durations = {}


      for (
        const module of data.modules || []
      ) {

        for (
          const lesson of module.lessons || []
        ) {

          durations[lesson.id] =
            lesson.duration || '00:00'

        }

      }


      setDurationValues(durations)

    } catch (err) {

      console.error(
        'Course loading error:',
        err
      )


      setError(
        err.message ||
        'Unable to load course'
      )

    } finally {

      setLoading(false)

    }

  }



  useEffect(() => {

    loadCourse()

  }, [courseId])



  // =====================================================
  // CURRENT COURSE DATA
  // =====================================================

  const course =
    courseData?.course

  const modules =
    courseData?.modules || []



  // =====================================================
  // START EDITING COURSE
  // =====================================================

  function startEditingCourse() {

    setCourseTitle(
      course?.title || ''
    )

    setCourseLevel(
      course?.level || 'Beginner'
    )

    setCourseDescription(
      course?.description || ''
    )

    setEditingCourse(true)

  }



  // =====================================================
  // SAVE COURSE CHANGES
  // =====================================================

  async function saveCourseChanges() {

    if (!courseTitle.trim()) {

      alert(
        'Please enter a course title'
      )

      return

    }


    try {

      setSavingCourse(true)


      await apiRequest(
        `/api/trainer/courses/${courseId}`,
        {
          method: 'PUT',

          body: JSON.stringify({
            title:
              courseTitle.trim(),

            level:
              courseLevel,

            description:
              courseDescription.trim()
          })
        }
      )


      showNotification(
        'Course updated successfully',
        'success'
      )


      setEditingCourse(false)


      await loadCourse()

    } catch (err) {

      console.error(
        'Course update error:',
        err
      )


      showNotification(
        err.message ||
        'Unable to update course'
      )

    } finally {

      setSavingCourse(false)

    }

  }



  // =====================================================
  // CANCEL COURSE EDIT
  // =====================================================

  function cancelEditingCourse() {

    setEditingCourse(false)

  }

    // =====================================================
  // START EDITING MODULE
  // =====================================================

  function startEditingModule(module) {

    setEditingModule(module.id)

    setModuleTitle(
      module.module || ''
    )

  }



  // =====================================================
  // CANCEL MODULE EDIT
  // =====================================================

  function cancelEditingModule() {

    setEditingModule(null)

    setModuleTitle('')

  }



  // =====================================================
  // SAVE MODULE CHANGES
  // =====================================================

  async function saveModuleChanges(module) {

    if (!moduleTitle.trim()) {

      alert(
        'Please enter a module name'
      )

      return

    }


    try {

      setSavingModule(
        module.id
      )


      await apiRequest(
        `/api/trainer/modules/${module.id}`,
        {
          method: 'PUT',

          body: JSON.stringify({
            title:
              moduleTitle.trim()
          })
        }
      )


      showNotification(
        'Module updated successfully',
        'success'
      )


      setEditingModule(null)

      setModuleTitle('')

      await loadCourse()

    } catch (err) {

      console.error(
        'Module update error:',
        err
      )


      showNotification(
        err.message ||
        'Unable to update module'
      )

    } finally {

      setSavingModule(null)

    }

  }



  // =====================================================
  // GET REAL VIDEO DURATION
  // =====================================================

  async function getVideoDuration(file) {

    const videoElement =
      document.createElement('video')


    const videoUrl =
      URL.createObjectURL(file)


    videoElement.preload =
      'metadata'

    videoElement.src =
      videoUrl


    try {

      const durationInSeconds =
        await new Promise(
          (resolve, reject) => {

            videoElement.onloadedmetadata =
              () => {

                resolve(
                  videoElement.duration
                )

              }


            videoElement.onerror =
              () => {

                reject(
                  new Error(
                    'Unable to read video duration'
                  )
                )

              }

          }
        )


      return durationInSeconds

    } finally {

      URL.revokeObjectURL(
        videoUrl
      )

    }

  }



  // =====================================================
  // FORMAT VIDEO DURATION
  // =====================================================

  function formatDuration(
    durationInSeconds
  ) {

    const totalSeconds =
      Math.round(
        durationInSeconds
      )


    const hours =
      Math.floor(
        totalSeconds / 3600
      )


    const minutes =
      Math.floor(
        (totalSeconds % 3600) / 60
      )


    const seconds =
      totalSeconds % 60


    if (hours > 0) {

      return (
        `${String(hours).padStart(2, '0')}:` +
        `${String(minutes).padStart(2, '0')}:` +
        `${String(seconds).padStart(2, '0')}`
      )

    }


    return (
      `${String(minutes).padStart(2, '0')}:` +
      `${String(seconds).padStart(2, '0')}`
    )

  }



  // =====================================================
  // UPLOAD VIDEO
  // =====================================================

  async function handleVideoUpload(
    lesson,
    file
  ) {

    if (!file) {
      return
    }


    try {

      setUploadingVideo(
        lesson.id
      )


      // -------------------------------------------------
      // Read actual video duration
      // -------------------------------------------------

      const durationInSeconds =
        await getVideoDuration(
          file
        )


      const formattedDuration =
        formatDuration(
          durationInSeconds
        )


      // -------------------------------------------------
      // Upload video
      // -------------------------------------------------

      const formData =
        new FormData()


      formData.append(
        'video',
        file
      )


      const response =
        await apiRequest(
          `/api/trainer/lessons/${lesson.id}/video`,
          {
            method: 'POST',
            body: formData
          }
        )


      console.log(
        'VIDEO UPLOAD RESPONSE:',
        response
      )


      // -------------------------------------------------
      // Save real duration
      // -------------------------------------------------

      await apiRequest(
        `/api/trainer/lessons/${lesson.id}/duration`,
        {
          method: 'PUT',

          body: JSON.stringify({
            duration:
              formattedDuration
          })
        }
      )


      showNotification(
        `Video uploaded successfully!\nDuration: ${formattedDuration}`,
        'success'
      )


      await loadCourse()

    } catch (err) {

      console.error(
        'Video upload error:',
        err
      )


      showNotification(
        err.message ||
        'Unable to upload video'
      )

    } finally {

      setUploadingVideo(null)

    }

  }



  // =====================================================
  // UPLOAD PDF
  // =====================================================

  async function handlePdfUpload(
    lesson,
    file
  ) {

    if (!file) {
      return
    }


    try {

      setUploadingPdf(
        lesson.id
      )


      const formData =
        new FormData()


      formData.append(
        'pdf',
        file
      )


      const response =
        await apiRequest(
          `/api/trainer/lessons/${lesson.id}/pdf`,
          {
            method: 'POST',
            body: formData
          }
        )


      console.log(
        'PDF UPLOAD RESPONSE:',
        response
      )


      showNotification(
        `PDF uploaded successfully!\n${file.name}`,
        'success'
      )

      await loadCourse()

    } catch (err) {

      console.error(
        'PDF upload error:',
        err
      )


      showNotification(
        err.message ||
        'Unable to upload PDF'
      )

    } finally {

      setUploadingPdf(null)

    }

  }



  // =====================================================
  // SAVE DURATION
  // =====================================================

  async function saveDuration(
    lesson
  ) {

    const duration =
      durationValues[lesson.id] ||
      ''


    if (!duration.trim()) {

      alert(
        'Please enter a duration'
      )

      return

    }


    try {

      setSavingDuration(
        lesson.id
      )


      await apiRequest(
        `/api/trainer/lessons/${lesson.id}/duration`,
        {
          method: 'PUT',

          body: JSON.stringify({
            duration:
              duration.trim()
          })
        }
      )


      showNotification(
        'Duration saved successfully',
        'success'
      )


      await loadCourse()

    } catch (err) {

      console.error(
        'Duration update error:',
        err
      )


      showNotification(
        err.message ||
        'Unable to save duration'
      )

    } finally {

      setSavingDuration(null)

    }

  }



  // =====================================================
  // VIEW RESOURCE
  // =====================================================

  async function handleViewResource(
    resource
  ) {

    try {

      setOpeningResource(
        resource.fileName
      )

      console.log(
      'RESOURCE URL:',
        resource.url
      )
      const blob =
        await fetchAuthenticatedBlob(
          resource.url
        )


      const blobUrl =
        URL.createObjectURL(
          blob
        )


      const newWindow =
        window.open(
          blobUrl,
          '_blank'
        )


      if (!newWindow) {

        URL.revokeObjectURL(
          blobUrl
        )


        alert(
          'Please allow pop-ups for this site to view the file.'
        )

        return

      }


      setTimeout(() => {

        URL.revokeObjectURL(
          blobUrl
        )

      }, 60000)

    } catch (err) {

      console.error(
        'Resource view error:',
        err
      )


      showNotification(
        err.message ||
        'Unable to open resource'
      )

    } finally {

      setOpeningResource(null)

    }

  }



  // =====================================================
  // DELETE RESOURCE
  // =====================================================

  async function handleDeleteResource(
    lesson,
    resource
  ) {

    const resourceName =
      resource.fileName


    const resourceType =
      resource.type === 'video'
        ? 'video'
        : 'PDF'


    const confirmed =
      window.confirm(
        `Remove this ${resourceType}?\n\n${resourceName}\n\nThis file will be permanently deleted.`
      )


    if (!confirmed) {
      return
    }


    const deleteKey =
      `${lesson.id}-${resource.type}-${resource.fileName}`


    try {

      setDeletingResource(
        deleteKey
      )


      await apiRequest(
        `/api/trainer/lessons/${lesson.id}/resources/${resource.type}/${encodeURIComponent(resource.fileName)}`,
        {
          method: 'DELETE'
        }
      )


      showNotification(
        `${resourceType} removed successfully`,
        'success'
      )


      await loadCourse()

    } catch (err) {

      console.error(
        'Resource delete error:',
        err
      )


      showNotification(
        err.message ||
        'Unable to delete resource'
      )

    } finally {

      setDeletingResource(null)

    }

  }



  // =====================================================
  // LOADING
  // =====================================================

  if (loading) {

    return (

      <DashboardLayout role="trainer">

        <div
          className="card"
          style={{
            padding: 30,
            textAlign: 'center'
          }}
        >

          Loading course...

        </div>

      </DashboardLayout>

    )

  }



  // =====================================================
  // ERROR
  // =====================================================

  if (error) {

    return (

      <DashboardLayout role="trainer">

        <div
          className="card"
          style={{
            padding: 30
          }}
        >

          <h2>
            Unable to load course
          </h2>


          <p>
            {error}
          </p>


          <Link
            to="/trainer"
            className="btn btn-primary"
          >
            ← Back to Trainer Dashboard
          </Link>

        </div>

      </DashboardLayout>

    )

  }



  // =====================================================
  // PAGE
  // =====================================================

  return (

    <DashboardLayout role="trainer">


      {/* =================================================
          HEADER
      ================================================= */}

      <div
        className="page-heading-row"
      >

        <div>

          <h1>
            {course?.title}
          </h1>


          <p>
            Manage and review your course content.
          </p>

        </div>


        <Link
          to="/trainer"
          className="btn btn-outline"
        >
          ← Dashboard
        </Link>

      </div>



      {/* =================================================
          COURSE INFORMATION
      ================================================= */}

      <div
        className="card"
        style={{
          padding: 22,
          marginBottom: 20
        }}
      >

        {!editingCourse ? (

          <>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                gap: 15,
                flexWrap: 'wrap'
              }}
            >

              <div>

                <h2
                  style={{
                    marginTop: 0
                  }}
                >
                  {course?.title}
                </h2>


                <p
                  style={{
                    marginTop: 8
                  }}
                >
                  {course?.description ||
                    'No description added.'}
                </p>

              </div>


              <button
                type="button"
                className="btn btn-primary"
                onClick={
                  startEditingCourse
                }
              >
                ✏️ Edit Course
              </button>

            </div>


            <div
              style={{
                display: 'flex',
                gap: 20,
                marginTop: 16,
                flexWrap: 'wrap'
              }}
            >

              <span>

                <strong>
                  Instructor:
                </strong>{' '}

                {course?.trainer ||
                  'Not assigned'}

              </span>


              <span>

                <strong>
                  Level:
                </strong>{' '}

                {course?.level}

              </span>


              <span>

                <strong>
                  Modules:
                </strong>{' '}

                {modules.length}

              </span>

            </div>

          </>

        ) : (

          <>
            <h2
              style={{
                marginTop: 0
              }}
            >
              Edit Course
            </h2>


            {/* COURSE TITLE */}

            <div
              className="field"
              style={{
                marginTop: 18
              }}
            >

              <label>
                Course Title
              </label>


              <input
                type="text"
                value={courseTitle}
                onChange={(e) =>
                  setCourseTitle(
                    e.target.value
                  )
                }
                placeholder="Enter course title"
              />

            </div>


            {/* DIFFICULTY LEVEL */}

            <div
              className="field"
            >

              <label>
                Difficulty Level
              </label>


              <select
                value={courseLevel}
                onChange={(e) =>
                  setCourseLevel(
                    e.target.value
                  )
                }
              >

                <option value="Beginner">
                  Beginner
                </option>

                <option value="Intermediate">
                  Intermediate
                </option>

                <option value="Advanced">
                  Advanced
                </option>

              </select>

            </div>


            {/* DESCRIPTION */}

            <div
              className="field"
            >

              <label>
                Course Description
              </label>


              <textarea
                rows={5}
                value={courseDescription}
                onChange={(e) =>
                  setCourseDescription(
                    e.target.value
                  )
                }
                placeholder="Describe your course..."
              />

            </div>


            {/* SAVE / CANCEL */}

            <div
              style={{
                display: 'flex',
                gap: 10,
                marginTop: 18,
                flexWrap: 'wrap'
              }}
            >

              <button
                type="button"
                className="btn btn-primary"
                disabled={
                  savingCourse
                }
                onClick={
                  saveCourseChanges
                }
              >

                {savingCourse
                  ? 'Saving...'
                  : '💾 Save Changes'}

              </button>


              <button
                type="button"
                className="btn btn-outline"
                disabled={
                  savingCourse
                }
                onClick={
                  cancelEditingCourse
                }
              >
                Cancel
              </button>

            </div>

          </>

        )}

      </div>



      {/* =================================================
          COURSE CONTENT
      ================================================= */}

      <div
        className="card"
        style={{
          padding: 22
        }}
      >

        <div
          className="section-title"
        >
          Course Content
        </div>



        {modules.length === 0 ? (

          <p
            style={{
              marginTop: 15
            }}
          >
            No modules have been added to this course yet.
          </p>

        ) : (

          <div
            style={{
              marginTop: 15
            }}
          >

            {modules.map(
              (module, index) => (

                <div
                  key={module.id}
                  style={{
                    border:
                      '1px solid var(--border)',
                    borderRadius: 10,
                    padding: 16,
                    marginBottom: 12
                  }}
                >

                  {/* =====================================
                      MODULE
                  ===================================== */}

                  <div
  style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap'
  }}
>

  {editingModule === module.id ? (

    <div
      style={{
        display: 'flex',
        gap: 8,
        alignItems: 'center',
        flex: 1,
        flexWrap: 'wrap'
      }}
    >

      <input
        type="text"
        value={moduleTitle}
        onChange={(e) =>
          setModuleTitle(
            e.target.value
          )
        }
        placeholder="Enter module name"
        style={{
          flex: 1,
          minWidth: 220,
          padding: '9px 10px',
          border:
            '1px solid var(--border)',
          borderRadius: 6
        }}
      />


      <button
        type="button"
        className="btn btn-primary"
        disabled={
          savingModule === module.id
        }
        onClick={() =>
          saveModuleChanges(module)
        }
      >

        {savingModule === module.id
          ? 'Saving...'
          : '💾 Save'}

      </button>


      <button
        type="button"
        className="btn btn-outline"
        disabled={
          savingModule === module.id
        }
        onClick={
          cancelEditingModule
        }
      >
        Cancel
      </button>

    </div>

  ) : (

    <>
      <h3
        style={{
          margin: 0
        }}
      >
        Module {index + 1}:{' '}
        {module.module}
      </h3>


      <button
        type="button"
        className="btn btn-outline"
        onClick={() =>
          startEditingModule(module)
        }
      >
        ✏️ Edit Module
      </button>
    </>

  )}

</div>



                  {/* =====================================
                      LESSONS
                  ===================================== */}

                  <div
                    style={{
                      marginTop: 12
                    }}
                  >

                  {!module.lessons || module.lessons.length === 0 ? (
  <p>No lessons in this module.</p>
) : (

                      module.lessons.map(
                        (
                          lesson,
                          lessonIndex
                        ) => {

                          const resources =
                            lesson.resources || []


                          const videos =
                            resources.filter(
                              (resource) =>
                                resource.type ===
                                'video'
                            )


                          const pdfs =
                            resources.filter(
                              (resource) =>
                                resource.type ===
                                'pdf'
                            )


                          return (

                            <div
                              key={lesson.id}
                              style={{
                                padding:
                                  '18px 0',

                                borderBottom:
                                  lessonIndex !==
                                  module.lessons.length - 1
                                    ? '1px solid var(--border)'
                                    : 'none'
                              }}
                            >

                              {/* =================================
                                  LESSON TITLE
                              ================================= */}

                              <strong
                                style={{
                                  fontSize: 15
                                }}
                              >

                                {lessonIndex + 1}.{' '}

                                {lesson.title}

                              </strong>



                              {/* =================================
                                  DURATION
                              ================================= */}

                              <div
                                style={{
                                  marginTop: 8
                                }}
                              >

                                <div
                                  style={{
                                    fontSize: 13,
                                    color:
                                      'var(--text-500)',
                                    marginBottom: 6
                                  }}
                                >
                                  Duration
                                </div>


                                <div
                                  style={{
                                    display: 'flex',
                                    gap: 8,
                                    flexWrap:
                                      'wrap'
                                  }}
                                >

                                  <input
                                    type="text"
                                    value={
                                      durationValues[
                                        lesson.id
                                      ] ||
                                      ''
                                    }
                                    placeholder="MM:SS"
                                    onChange={
                                      (e) =>
                                        setDurationValues(
                                          (previous) => ({
                                            ...previous,
                                            [lesson.id]:
                                              e.target.value
                                          })
                                        )
                                    }
                                    style={{
                                      width: 120,
                                      padding:
                                        '8px 10px',
                                      border:
                                        '1px solid var(--border)',
                                      borderRadius:
                                        6
                                    }}
                                  />


                                  <button
                                    type="button"
                                    className="btn btn-outline"
                                    disabled={
                                      savingDuration ===
                                      lesson.id
                                    }
                                    onClick={() =>
                                      saveDuration(
                                        lesson
                                      )
                                    }
                                  >

                                    {savingDuration ===
                                    lesson.id
                                      ? 'Saving...'
                                      : 'Save Duration'}

                                  </button>

                                </div>

                              </div>



                              {/* =================================
                                  VIDEOS
                              ================================= */}

                              <div
                                style={{
                                  marginTop: 15
                                }}
                              >

                                <div
                                  style={{
                                    fontWeight: 600,
                                    fontSize: 14,
                                    marginBottom: 8
                                  }}
                                >
                                  🎥 Videos
                                </div>


                                {videos.length === 0 ? (

                                  <div
                                    style={{
                                      fontSize: 13,
                                      color:
                                        'var(--text-500)',
                                      marginBottom: 8
                                    }}
                                  >
                                    No videos uploaded yet.
                                  </div>

                                ) : (

                                  <div
                                    style={{
                                      display:
                                        'flex',
                                      flexDirection:
                                        'column',
                                      gap: 8
                                    }}
                                  >

                                    {videos.map(
                                      (resource) => {

                                        const deleteKey =
                                          `${lesson.id}-${resource.type}-${resource.fileName}`


                                        return (

                                          <div
                                            key={
                                              resource.fileName
                                            }
                                            style={{
                                              display:
                                                'flex',
                                              alignItems:
                                                'center',
                                              justifyContent:
                                                'space-between',
                                              gap: 10,
                                              flexWrap:
                                                'wrap',
                                              padding:
                                                '10px 12px',
                                              background:
                                                'var(--surface-2)',
                                              borderRadius:
                                                8
                                            }}
                                          >

                                            <div
                                              style={{
                                                display:
                                                  'flex',
                                                alignItems:
                                                  'center',
                                                gap: 8,
                                                minWidth: 0
                                              }}
                                            >

                                              <span>
                                                🎥
                                              </span>


                                              <span
                                                style={{
                                                  fontSize: 13,
                                                  wordBreak:
                                                    'break-word'
                                                }}
                                              >
                                                {
                                                  resource.fileName
                                                }
                                              </span>

                                            </div>


                                            <div
                                              style={{
                                                display:
                                                  'flex',
                                                gap: 6,
                                                flexWrap:
                                                  'wrap'
                                              }}
                                            >

                                              <button
                                                type="button"
                                                className="btn btn-outline"
                                                disabled={
                                                  openingResource ===
                                                  resource.fileName
                                                }
                                                onClick={() =>
                                                  handleViewResource(
                                                    resource
                                                  )
                                                }
                                              >

                                                {openingResource ===
                                                resource.fileName
                                                  ? 'Opening...'
                                                  : '▶ View'}

                                              </button>


                                              <button
                                                type="button"
                                                className="btn btn-outline"
                                                disabled={
                                                  deletingResource ===
                                                  deleteKey
                                                }
                                                onClick={() =>
                                                  handleDeleteResource(
                                                    lesson,
                                                    resource
                                                  )
                                                }
                                                style={{
                                                  color:
                                                    '#c62828'
                                                }}
                                              >

                                                {deletingResource ===
                                                deleteKey
                                                  ? 'Removing...'
                                                  : '🗑 Remove'}

                                              </button>

                                            </div>

                                          </div>

                                        )

                                      }
                                    )}

                                  </div>

                                )}



                                {/* ADD MORE VIDEO */}

                                <label
                                  className="btn btn-outline"
                                  style={{
                                    display:
                                      'inline-block',
                                    marginTop: 10,
                                    cursor:
                                      uploadingVideo ===
                                      lesson.id
                                        ? 'wait'
                                        : 'pointer'
                                  }}
                                >

                                  {uploadingVideo ===
                                  lesson.id
                                    ? '⏳ Uploading Video...'
                                    : '➕ Add More Video'}


                                  <input
                                    type="file"
                                    accept="video/mp4,video/webm,video/quicktime,video/*"
                                    hidden
                                    disabled={
                                      uploadingVideo ===
                                      lesson.id
                                    }
                                    onChange={(e) => {

                                      const file =
                                        e.target.files?.[0]


                                      if (file) {

                                        handleVideoUpload(
                                          lesson,
                                          file
                                        )

                                      }


                                      e.target.value =
                                        ''

                                    }}
                                  />

                                </label>

                              </div>



                              {/* =================================
                                  PDFS
                              ================================= */}

                              <div
                                style={{
                                  marginTop: 18
                                }}
                              >

                                <div
                                  style={{
                                    fontWeight: 600,
                                    fontSize: 14,
                                    marginBottom: 8
                                  }}
                                >
                                  📄 PDFs
                                </div>


                                {pdfs.length === 0 ? (

                                  <div
                                    style={{
                                      fontSize: 13,
                                      color:
                                        'var(--text-500)',
                                      marginBottom: 8
                                    }}
                                  >
                                    No PDFs uploaded yet.
                                  </div>

                                ) : (

                                  <div
                                    style={{
                                      display:
                                        'flex',
                                      flexDirection:
                                        'column',
                                      gap: 8
                                    }}
                                  >

                                    {pdfs.map(
                                      (resource) => {

                                        const deleteKey =
                                          `${lesson.id}-${resource.type}-${resource.fileName}`


                                        return (

                                          <div
                                            key={
                                              resource.fileName
                                            }
                                            style={{
                                              display:
                                                'flex',
                                              alignItems:
                                                'center',
                                              justifyContent:
                                                'space-between',
                                              gap: 10,
                                              flexWrap:
                                                'wrap',
                                              padding:
                                                '10px 12px',
                                              background:
                                                'var(--surface-2)',
                                              borderRadius:
                                                8
                                            }}
                                          >

                                            <div
                                              style={{
                                                display:
                                                  'flex',
                                                alignItems:
                                                  'center',
                                                gap: 8,
                                                minWidth: 0
                                              }}
                                            >

                                              <span>
                                                📄
                                              </span>


                                              <span
                                                style={{
                                                  fontSize: 13,
                                                  wordBreak:
                                                    'break-word'
                                                }}
                                              >
                                                {
                                                  resource.fileName
                                                }
                                              </span>

                                            </div>


                                            <div
                                              style={{
                                                display:
                                                  'flex',
                                                gap: 6,
                                                flexWrap:
                                                  'wrap'
                                              }}
                                            >

                                              <button
                                                type="button"
                                                className="btn btn-outline"
                                                disabled={
                                                  openingResource ===
                                                  resource.fileName
                                                }
                                                onClick={() =>
                                                  handleViewResource(
                                                    resource
                                                  )
                                                }
                                              >

                                                {openingResource ===
                                                resource.fileName
                                                  ? 'Opening...'
                                                  : '👁 View'}

                                              </button>


                                              <button
                                                type="button"
                                                className="btn btn-outline"
                                                disabled={
                                                  deletingResource ===
                                                  deleteKey
                                                }
                                                onClick={() =>
                                                  handleDeleteResource(
                                                    lesson,
                                                    resource
                                                  )
                                                }
                                                style={{
                                                  color:
                                                    '#c62828'
                                                }}
                                              >

                                                {deletingResource ===
                                                deleteKey
                                                  ? 'Removing...'
                                                  : '🗑 Remove'}

                                              </button>

                                            </div>

                                          </div>

                                        )

                                      }
                                    )}

                                  </div>

                                )}



                                {/* ADD MORE PDF */}

                                <label
                                  className="btn btn-outline"
                                  style={{
                                    display:
                                      'inline-block',
                                    marginTop: 10,
                                    cursor:
                                      uploadingPdf ===
                                      lesson.id
                                        ? 'wait'
                                        : 'pointer'
                                  }}
                                >

                                  {uploadingPdf ===
                                  lesson.id
                                    ? '⏳ Uploading PDF...'
                                    : '➕ Add More PDF'}


                                  <input
                                    type="file"
                                    accept="application/pdf"
                                    hidden
                                    disabled={
                                      uploadingPdf ===
                                      lesson.id
                                    }
                                    onChange={(e) => {

                                      const file =
                                        e.target.files?.[0]


                                      if (file) {

                                        handlePdfUpload(
                                          lesson,
                                          file
                                        )

                                      }


                                      e.target.value =
                                        ''

                                    }}
                                  />

                                </label>

                              </div>

                            </div>

                          )

                        }
                      )

                    )}

                  </div>

                </div>

              )
            )}

          </div>

        )}

      </div>

    </DashboardLayout>

  )

}