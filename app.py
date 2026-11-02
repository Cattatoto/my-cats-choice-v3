for attempt in range(3):
                        try:
                            result = client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=contents
                            )
                            result_text = result.text
                            provider_used = "Gemini"
                            break

                        except Exception as e:
                            gemini_error = e
                            error_text = str(e).upper()
                            is_temporary = (
                                "503" in error_text
                                or "UNAVAILABLE" in error_text
                                or "429" in error_text
                                or "RESOURCE_EXHAUSTED" in error_text
                            )
                            if is_temporary and attempt < 2:
                                time.sleep(5 * (attempt + 1))
                            else:
                                break

                    # Groq vision accepts up to 3 images per request.
                    if result_text is None:
                        groq_api_key = st.secrets.get("GROQ_API_KEY", "")

                        if not groq_api_key:
                            raise RuntimeError(
                                f"Gemini failed ({gemini_error}). "
                                "Groq backup key is missing from Streamlit Secrets."
                            )

                        st.info("Gemini is unavailable. Trying the Groq backup...")

                        # Always include at least one image from each product,
                        # then include up to one additional image (3 total).
                        selected_images = [images_a[0], images_b[0]]
                        remaining_images = images_a[1:] + images_b[1:]
                        selected_images.extend(remaining_images[:1])

                        message_content = [
                            {
                                "type": "text",
                                "text": (
                                    prompt
                                    + "\\n\\nBACKUP IMAGE NOTE: "
                                    + f"Groq is receiving {len(selected_images)} selected photos "
                                    + "because this vision model accepts at most 3 images per request. "
                                    + "Base your conclusions only on the photos supplied."
                                )
                            }
                        ]

                        for img in selected_images:
                            buffer = BytesIO()
                            img.convert("RGB").save(
                                buffer, format="JPEG", quality=85, optimize=True
                            )
                            encoded_image = base64.b64encode(
                                buffer.getvalue()
                            ).decode("utf-8")
                            message_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded_image}"
                                }
                            })

                        groq_response = requests.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {groq_api_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": "qwen/qwen3.8-27b",
                                "messages": [
                                    {"role": "user", "content": message_content}
                                ],
                                "temperature": 0.3,
                                "max_completion_tokens": 6000
                            },
                            timeout=120
                        )
                        groq_response.raise_for_status()
                        groq_data = groq_response.json()
                        result_text = groq_data["choices"][0]["message"]["content"]
                        provider_used = "Groq"

                    st.success(f"🎉 Comparison completed using {provider_used}!")

                    st.subheader(t[10])
                    st.markdown(result_text)

                    st.caption(
                        "🐱 AI-generated information may contain errors. "
                        "Please verify product labels and important claims."
                    )

                except Exception as e:
                    st.error(f"⚠️ Comparison error: {e}")

st.divider()
st.markdown(
    "<p style='text-align:center;color:#a64d79'>"
    "🐾 My Cat's Choice 3.0 | Made with love 🌸"
    "</p>",
    unsafe_allow_html=True
)
