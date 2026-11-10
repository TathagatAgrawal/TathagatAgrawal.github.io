// Builds one resume. `uv run resume <name>` passes the resume's name and, as the `data` input, everything it
// shows (built by src/portfolio/resume_data.py from content/config.yaml and the content files).
#import "lib.typ": resume

#show: resume.with(json(bytes(sys.inputs.data)))
