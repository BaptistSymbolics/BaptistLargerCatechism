-- catechism-filter.lua
-- A Pandoc Lua filter to transform Markdown divs into LaTeX environments

-- Function to handle the catechism question divs
function handle_question(div)
    if div.classes:includes("catechism-question") then
      -- Extract content and create custom LaTeX environment
      local content = pandoc.utils.stringify(div.content)
      local latex = "\\begin{catechismQuestion}\n" .. content .. "\n\\end{catechismQuestion}"
      
      -- Return raw LaTeX block
      return pandoc.RawBlock("latex", latex)
    end
  end
  
  -- Function to handle the catechism answer divs
  function handle_answer(div)
    if div.classes:includes("catechism-answer") then
      -- Extract content and create custom LaTeX environment
      local content = pandoc.utils.stringify(div.content)
      local latex = "\\begin{catechismAnswer}\n" .. content .. "\n\\end{catechismAnswer}"
      
      -- Return raw LaTeX block
      return pandoc.RawBlock("latex", latex)
    end
  end
  
-- Function to handle the scripture references divs
function handle_references(div)
    if div.classes:includes("scripture-references") then
      -- Get the number of columns (default to 2 if not specified)
      local columns = div.attributes.columns or "2"
      
      -- Extract content
      local content = pandoc.write(div.content, "latex")
      
      -- Create custom LaTeX environment with multicols
      local latex = "\\begin{scriptureReferences}{" .. columns .. "}\n" 
                    .. content 
                    .. "\n\\end{scriptureReferences}"
      
      -- Return raw LaTeX block
      return pandoc.RawBlock("latex", latex)
    end
  end
  
  -- Return the filter as a list of element handlers
  return {
    Div = function(div)
      -- Try each handler in sequence
      return handle_question(div) or handle_answer(div) or handle_references(div) or div
    end
  }